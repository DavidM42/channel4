#!/usr/bin/env python3
"""Updates the firmware of a board over WiFi.

    python3 web/execute_reflash.py 192.168.1.50
    python3 web/execute_reflash.py 192.168.1.50 image.elf-0x00000.bin image.elf-0x10000.bin

The board has to run this firmware already and be on your network.  The two images are first put into a part of the
flash the firmware does not use, read back and compared.  Only then the board is told to copy them over its firmware,
and it checks them once more itself before it does.  Afterwards the flash is read back again.

If the power fails while the board copies (about ten seconds), it does not start any more and has to be flashed over
USB.  Everything before that step changes nothing, --dry-run stops there.

The web page (page.mpfs) and the settings stay as they are.
"""

import argparse
import hashlib
import os
import socket
import sys
import time

PORT = 7878                              # BACKEND_PORT of the firmware
STAGE1, STAGE2 = 0x0B0000, 0x0C0000      # where the new images wait until they are copied
DEST1, DEST2 = 0x000000, 0x010000        # where the firmware lives
CHUNK = 1024                             # the firmware wants the images in pieces of this size, padded with zeros
BLOCK = 65536                            # what one "erase block" command erases
STAGE1_ROOM = STAGE2 - STAGE1            # image 1 has to fit below image 2
STAGE2_ROOM = 0x100000 - STAGE2          # the board checks the staged images through its first megabyte of flash

REFUSALS = {
    2: "it did not understand the command",
    3: "an address is not on a sector boundary",
    4: "image 1 did not arrive intact",
    5: "image 2 did not arrive intact",
}


class Stop(Exception):
    """Something went wrong.  The text says what, and whether the board was changed."""


class Board:
    def __init__(self, ip):
        self.addr = (ip, PORT)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.repeats = 0        # how often a command had to be sent again
        self.last_tries = 0     # how many times the last command was sent

    def ask(self, packet, expect, tries=30, wait=1.0):
        """Sends a command until a reply that starts with "expect" comes back.  Returns the reply, or None.
        WiFi to these boards can be poor, so this is patient: by default it keeps trying for half a minute."""
        for attempt in range(tries):
            self.last_tries = attempt + 1
            self.repeats += attempt > 0
            self.send(packet)
            reply = self.listen(expect, wait)
            if reply is not None:
                return reply
        return None

    def send(self, packet):
        try:
            self.sock.sendto(packet, self.addr)
        except OSError:
            pass   # no route for a moment, for example while the board restarts

    def listen(self, expect, wait):
        """Waits for a reply that starts with "expect", without sending anything."""
        end = time.time() + wait
        while True:
            left = end - time.time()
            if left <= 0:
                return None
            self.sock.settimeout(left)
            try:
                reply, _ = self.sock.recvfrom(4096)
            except socket.timeout:
                return None
            except OSError:
                time.sleep(0.2)
                continue
            if reply.startswith(expect):
                return reply

    def read(self, addr, length, tries=30):
        """Reads flash.  The length has to be a multiple of 4 and at most 1280."""
        head = b"FR%08d\t%04d\t" % (addr, length)
        reply = self.ask(b"FR%d\t%d" % (addr, length), head, tries)
        if reply is None or len(reply) < len(head) + length:
            return None
        return reply[len(head):len(head) + length]

    def read_all(self, addr, length, when_poor=None):
        """Reads a stretch of flash.  when_poor gets called once if the board is slow to answer."""
        data = b""
        for off in range(0, length, CHUNK):
            piece = self.read(addr + off, min(CHUNK, length - off))
            if piece is None:
                raise Stop("The board stopped answering while its flash was read at 0x%06x.\n"
                           "Nothing was changed.  Try again, closer to the access point if you can." % (addr + off))
            data += piece
            if when_poor and self.last_tries >= 3:
                when_poor()
                when_poor = None
        return data

    def answers(self):
        return self.read(DEST1, 16, tries=1) is not None

    def stage(self, base, data, label):
        erased = -1
        for off in range(0, len(data), CHUNK):
            addr = base + off
            if addr // BLOCK != erased:
                erased = addr // BLOCK
                if not self.ask(b"FB%d\r\n" % erased, b"FB%d" % erased):
                    raise Stop("The board did not confirm erasing block %d." % erased)
            if not self.ask(b"FW%d\t%d\t" % (addr, CHUNK) + data[off:off + CHUNK], b"FW%d" % addr):
                raise Stop("The board did not confirm writing at 0x%06x." % addr)
        print("  %s: %d bytes sent" % (label, len(data)))


def load(path):
    with open(path, "rb") as f:
        return f.read()


def padded(data):
    return data + b"\0" * (-len(data) % CHUNK)


def runs(board, file1, file2, when_poor=None):
    """Does the board's flash hold these two images?  The board keeps the first four bytes it has (among them how
    to talk to its flash chip, and how big it is), so those do not count."""
    flash1 = board.read_all(DEST1, len(padded(file1)), when_poor)
    flash2 = board.read_all(DEST2, len(padded(file2)), when_poor)
    return flash1[4:len(file1)] == file1[4:] and flash2[:len(file2)] == file2


def find_image(name, given):
    if given:
        return given
    for folder in (os.getcwd(), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")):
        path = os.path.join(folder, name)
        if os.path.exists(path):
            return path
    raise Stop("Cannot find %s.  Build the firmware first, or name the two image files." % name)


def update(args):
    if args.ip.upper() == "USB":
        raise Stop("Updating over USB is not something this firmware can do.  Give the board's network address.")

    path1 = find_image("image.elf-0x00000.bin", args.image1)
    path2 = find_image("image.elf-0x10000.bin", args.image2)
    file1, file2 = load(path1), load(path2)
    image1, image2 = padded(file1), padded(file2)
    board = Board(args.ip)
    quiet = []   # filled once the TV signal has been stopped

    def stop_signal(why="for the transfer"):
        # The TV signal on the RX pin disturbs the board's own WiFi.
        if args.keep_signal or quiet:
            return
        if board.ask(b"CS", b"CS", tries=5):
            quiet.append(True)
            print("TV signal stopped %s." % why)
        else:
            print("This firmware has no command to stop the TV signal, carrying on with it.")

    def signal_note():
        return "  The TV signal is off now, a text or demo command starts it again." if quiet else ""

    # --- Everything that can be checked before anything is sent ---

    if image1[:1] != b"\xe9":
        raise Stop("%s does not look like a firmware image." % path1)
    if len(image1) > STAGE1_ROOM or len(image2) > STAGE2_ROOM:
        raise Stop("The images are too big to update over WiFi (%d and %d bytes, room for %d and %d)."
                   % (len(image1), len(image2), STAGE1_ROOM, STAGE2_ROOM))

    print("Asking %s what it is running..." % args.ip)
    header = board.read(DEST1, 16, tries=5)
    if header is None:
        raise Stop("No answer from %s.  Is the board on the network, and does it run this firmware?" % args.ip)
    if header[:2] != image1[:2]:
        # The board keeps its own first four bytes, so a different number of segments would give an image that
        # does not start.
        raise Stop("The new image is laid out differently from the firmware on the board (%s against %s).\n"
                   "This one has to go on over USB." % (image1[:2].hex(), header[:2].hex()))

    if runs(board, file1, file2, lambda: stop_signal("because the board is slow to answer")) and not args.force:
        print("The board already runs exactly this firmware.  Nothing to do.%s" % signal_note())
        return

    # --- Staging: none of this touches the running firmware ---

    stop_signal()
    print("Sending the new firmware to the spare part of the flash...")
    board.repeats = 0
    board.stage(STAGE1, image1, "image 1")
    board.stage(STAGE2, image2, "image 2")

    print("Reading it back...")
    if board.read_all(STAGE1, len(image1)) != image1 or board.read_all(STAGE2, len(image2)) != image2:
        raise Stop("What the board stored is not what was sent.  Nothing was changed, try again.%s" % signal_note())
    print("  identical" + ("  (%d packets had to be sent again, the WiFi link is poor)" % board.repeats
                           if board.repeats > 10 else ""))

    if args.dry_run:
        print("Dry run: stopping here.  The firmware on the board is untouched.%s" % signal_note())
        return

    # --- The one step that cannot be taken back ---

    command = b"FM%d\t%d\t%d\t%s\t%d\t%d\t%d\t%s\n" % (
        STAGE1, DEST1, len(image1), hashlib.md5(image1).hexdigest().encode(),
        STAGE2, DEST2, len(image2), hashlib.md5(image2).hexdigest().encode())
    print("Telling the board to copy it into place.  Do not cut its power now...")
    board.send(command)
    time.sleep(0.01)
    board.send(command)   # in case the first one got lost; a board that is copying does not hear it

    # A board that goes ahead says nothing.  One that refuses answers, and has changed nothing.
    refusal = board.listen(b"!FM", 4.0)
    if refusal is not None:
        code = int(refusal[3:4]) if refusal[3:4].isdigit() else 0
        raise Stop("The board refused: %s.  Nothing was changed." % REFUSALS.get(code, "reason %d" % code))

    # While it copies and restarts, the board does not answer.  Wait for it to go away, and then to come back.
    print("Waiting for the board to come back...")
    start = time.time()
    missed, was_away = 0, False
    while True:
        if board.answers():
            if was_away:
                break
            missed = 0
            if time.time() - start > 20:
                raise Stop("The board never started copying, the command got lost.  Nothing was changed, run this again.")
        else:
            missed += 1
            was_away = was_away or missed >= 2
        if time.time() - start > 120:
            raise Stop("The board did not come back within two minutes.\n"
                       "Power it off and on.  If it still does not show up, it has to be flashed over USB.")
        time.sleep(0.5)

    time.sleep(2)   # let it settle on the network
    if not runs(board, file1, file2):
        raise Stop("The board is back, but its flash is not the new firmware.")
    print("Done.  The board restarted and its flash is the new firmware.")


def main():
    parser = argparse.ArgumentParser(description="Updates the firmware of a board over WiFi.",
                                     epilog="Without image names it takes image.elf-0x00000.bin and "
                                            "image.elf-0x10000.bin from the current folder.")
    parser.add_argument("ip", help="network address of the board")
    parser.add_argument("image1", nargs="?", help="the image for 0x00000")
    parser.add_argument("image2", nargs="?", help="the image for 0x10000")
    parser.add_argument("--dry-run", action="store_true",
                        help="send and check the new firmware, but do not let the board switch to it")
    parser.add_argument("--force", action="store_true", help="update even if the board already runs this firmware")
    parser.add_argument("--keep-signal", action="store_true", help="do not stop the TV signal for the transfer")
    args = parser.parse_args()
    if bool(args.image1) != bool(args.image2):
        parser.error("give both images or none")

    try:
        update(args)
    except Stop as stop:
        sys.exit("\n%s" % stop)
    except KeyboardInterrupt:
        sys.exit("\nStopped.")


if __name__ == "__main__":
    main()
