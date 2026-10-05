# channel4

Analog broadcast television straight out of an ESP8266 pin, set up for black and white PAL TVs.

> ## This is cnlohr's work
>
> channel4 is a fork of **[cnlohr/channel3](https://github.com/cnlohr/channel3)** by Charles Lohr.
> The idea, the RF trick, the firmware, the 3D engine and the web interface are all his, and they are great.
> PAL line timing was also already in channel3, contributed there.
>
> This fork only adapts that work so it gives a solid picture on European black and white PAL sets, adds a few options around that, and explains how to build and flash it on a current Mac or Linux machine.
> The changes in this fork were made with the help of an AI coding assistant.
>
> If you have an NTSC TV, or you want color, use the original.

Solder a wire to the RX pin, flash the board, tune an old TV to channel E4 and watch a 3D demo that an ESP8266 is transmitting by toggling one pin.

## What is different from channel3

- **It broadcasts on European channel E4** (62.5 MHz) instead of US channel 3 (61.25 MHz), hence the name.
- **Black and white mode.** `MONOCHROME` leaves out all NTSC color information. The colors become clean shades of gray instead of hatching.
- **Optional bright border** for TVs that show dark screens as gray.
- **PAL and black and white are switched on by default** in `user.cfg`.
- **Setup, build and flash instructions** for macOS and Linux, below.

Everything else, including the web interface and the demo screens, is channel3.

## What you need

- **An ESP8266 board with USB and 4 MB of flash.** A Wemos D1 Mini is what this was built and tested on.
- **A USB cable that carries data.** Many micro USB cables only charge. If no serial port shows up, try another cable first.
- **A piece of wire** for the antenna, 20 to 30 cm to start with. See [Antenna](#antenna).
- **An analog TV that receives VHF band I** (often labeled VHF-L or VL) in the B/G standard used in most of continental Europe.
- **A Mac or a Linux PC.** macOS on Apple Silicon was used for everything here, including flashing. On Linux the setup and build steps were checked on Ubuntu 24.04. Flashing from Linux was not tried, it is the same esptool command.

## Setup, build and flash

The whole thing is six steps. Steps 1 and 2 are only needed once.

### 1. Install the tools

You need `git`, `make` and `esptool` in version 4.8.1.

**macOS** (with [Homebrew](https://brew.sh))

```sh
xcode-select --install                 # git and make, skip if you have them
brew install pipx
pipx install esptool==4.8.1
pipx ensurepath                        # then open a new terminal
softwareupdate --install-rosetta       # Apple Silicon only, the compiler is an Intel program
```

On a Mac you also need the driver for the USB serial chip on the board. The Wemos D1 Mini uses a CH340, and its maker WCH has the driver here: https://www.wch-ic.com/downloads/CH34XSER_MAC_ZIP.html
Download it, run the installer, and allow it if macOS asks you to in System Settings under Privacy & Security. On the Mac this was built on, the board did not show up as a serial port before the driver was installed.

Boards with a different USB serial chip (a CP2102 for example) need that chip's driver instead.

**Linux** (Debian, Ubuntu and relatives, on a 64-bit Intel or AMD PC)

```sh
sudo apt-get install git make gcc python3 pipx wget
pipx install esptool==4.8.1
pipx ensurepath                        # then open a new terminal
sudo usermod -aG dialout $USER         # lets you use the serial port, log out and in again afterwards
```

Linux needs no driver for the CH340, it comes with the kernel.

Check that it worked. This should print `4.8.1`:

```sh
esptool.py version
```

The version matters. `brew install esptool` and a plain `pipx install esptool` give you esptool 5, and the build stops there with `Specify the --chip argument`. If you need esptool 5 for other things, see [Troubleshooting](#troubleshooting).

### 2. Get the compiler

The ESP8266 needs its own compiler, `xtensa-lx106-elf-gcc`.
Espressif publishes a ready-made one, so there is nothing to build.
Put it in `~/esp8266`:

**macOS**

```sh
mkdir -p ~/esp8266 && cd ~/esp8266
curl -LO https://dl.espressif.com/dl/xtensa-lx106-elf-macos-1.22.0-100-ge567ec7-5.2.0.tar.gz
tar xzf xtensa-lx106-elf-macos-1.22.0-100-ge567ec7-5.2.0.tar.gz
```

**Linux**

```sh
mkdir -p ~/esp8266 && cd ~/esp8266
wget https://dl.espressif.com/dl/xtensa-lx106-elf-linux64-1.22.0-100-ge567ec7-5.2.0.tar.gz
tar xzf xtensa-lx106-elf-linux64-1.22.0-100-ge567ec7-5.2.0.tar.gz
```

Check that it worked. This should print `5.2.0`:

```sh
~/esp8266/xtensa-lx106-elf/bin/xtensa-lx106-elf-gcc -dumpversion
```

### 3. Get the source

```sh
git clone --recursive https://github.com/DavidM42/channel4.git
cd channel4
```

`--recursive` matters. Most of the build lives in a submodule (`esp82xx`), and without it `make` finds nothing to do.
If you already cloned without it, run `git submodule update --init --recursive`.

### 4. Build

Run this in the `channel4` folder:

```sh
make clean ESP_ROOT="$HOME/esp8266" ESP_GCC_VERS=5.2.0 ESPTOOL_PY=esptool.py
make all   ESP_ROOT="$HOME/esp8266" ESP_GCC_VERS=5.2.0 ESPTOOL_PY=esptool.py
```

The three settings tell the build where the compiler from step 2 is, which version it is, and to use the esptool from step 1.

You will see a lot of compiler warnings. That is normal.
It worked if the last line says `Successfully created esp8266 image.` and these two files exist:

```
image.elf-0x00000.bin
image.elf-0x10000.bin
```

Always run `make clean` before `make all` after you change `user.cfg`. The build does not notice changes in that file by itself.

### 5. Flash

Plug the board in and find its serial port.

| | Command | Typical port |
|---|---|---|
| macOS | `ls /dev/cu.*` | `/dev/cu.wchusbserial10` |
| Linux | `ls /dev/ttyUSB*` | `/dev/ttyUSB0` |

If nothing like that is listed, see [Troubleshooting](#troubleshooting). On a Mac the usual reasons are the missing driver from step 1 or a USB cable that only charges.

Put it in a variable so the commands below can be copied as they are:

```sh
PORT=/dev/ttyUSB0      # use your own port here
```

**The first time**, write everything: the firmware, the web page, and the settings area the ESP8266 system software needs.

```sh
esptool.py --port "$PORT" -b 460800 write_flash -fm dio -fs 4MB \
  0x00000  image.elf-0x00000.bin \
  0x10000  image.elf-0x10000.bin \
  0x80000  web/page.mpfs \
  0x3FB000 esp82xx/toolchain/esp_nonos_sdk/bin/blank.bin \
  0x3FC000 esp82xx/toolchain/esp_nonos_sdk/bin/esp_init_data_default_v08.bin \
  0x3FE000 esp82xx/toolchain/esp_nonos_sdk/bin/blank.bin
```

**After that**, when you only rebuilt the firmware, the first two files are enough:

```sh
esptool.py --port "$PORT" -b 460800 write_flash -fm dio -fs 4MB \
  0x00000 image.elf-0x00000.bin \
  0x10000 image.elf-0x10000.bin
```

It worked if every file ends with `Hash of data verified.`

Three things worth knowing:

- **`-fs 4MB` is required.** Without it the firmware believes it has 1 MB of flash and looks for its settings in the wrong place.
- **These addresses are for 4 MB of flash**, which is what a D1 Mini has. `esptool.py --port "$PORT" flash_id` tells you what your board has. Other sizes were not tested here.
- **Use these commands instead of `make burn`.** The make targets leave out `-fs 4MB`, and they report success even when flashing failed.

### 6. Watch TV

1. Connect the wire to the pin labeled **RX** (GPIO3) and power the board from any USB supply.
2. Switch the TV to VHF band I (VHF-L, VL) and tune to channel E4, 62.5 MHz. On a set with a tuning wheel, turn slowly through the lower part of the band until the picture appears.
3. Set brightness so the background of a text screen is just black, then contrast so the text is crisp.

The board also opens a WiFi network called `ESP_` followed by six characters. Join it and open http://192.168.4.1 for the web interface. Its "NTSC" button lets you freeze the demo on one screen, which makes adjusting the TV much easier.

## Options

All of these are lines in `user.cfg`. A `#` in front switches a line off.

| Line in `user.cfg` | What it does |
|---|---|
| `OPTS += -DPAL` | PAL timing: 625 lines, 50 fields per second. Off means NTSC. |
| `OPTS += -DMONOCHROME` | Black and white only. No colorburst, and the colors become shades of gray. |
| `OPTS += -DWHITE_BORDER` | Paints the visible area left, right and above the picture bright instead of black. |
| `OPTS += -DBORDER_LEVEL=13` | How bright that border is. Only used together with `WHITE_BORDER`. |

After changing any of them: `make clean`, `make all`, flash.

### Black and white only

On a black and white TV the NTSC color information only gets in the way. The colors show up as hatching, and the colorburst sits at a different level than black right where some TVs take their black reference.

With `MONOCHROME` there is no colorburst, and colors 0 to 15 become plain grays:

- 0 is black and 10 is white, as before.
- 2 and 8 are still the half black, half white ones that the sharp text uses.
- 3 to 7, 9 and 11 to 15 run from dark to bright.

A single pin can only be on or off, so only a few brightness levels come out clean. On channel E4 that is 8 grays between black and white, and some neighboring color numbers share a gray.

Both color tables live in `tablemaker/broadcast_tables.c`. The option picks one of them.

### Bright border

Many small TVs, most black and white portables among them, do not hold their black level. A mostly dark picture like the text screens comes out as light gray text on a slightly darker gray.

Try the brightness and contrast controls of the TV first. That is usually enough.

If it is not, `WHITE_BORDER` gives the TV something bright to go by on every screen, without taking anything away from the picture. White (`BORDER_LEVEL=10`, the default) works best but glows on a small tube. With `MONOCHROME`, 13 is a light gray and a good place to start.

The lines below the picture always stay black. Bright lines running right up to the vertical sync made the whole picture bounce on the TV this was tried on.

## Antenna

The antenna is a plain wire on the **RX** pin.

- **Start with 20 to 30 cm**, laid near the TV or its aerial. That is enough across a table or a room.
- **A full quarter wave is about 1.15 m** on channel E4. Only go there if the short wire gives a snowy picture.
- **Do not go longer than you need.** The pin puts out a raw 80 MHz bit stream. Next to the TV channel it also produces copies on other frequencies, one of them around 97.5 MHz in the FM radio band. A longer wire radiates all of them further, and you have no license for any of them. Keep it on your desk.

For other channels, a quarter wave in meters is about 71 divided by the frequency in MHz.

**The antenna can block flashing.** RX is also the pin the USB chip uses to talk to the ESP8266. A wire hanging free is no problem. A wire that is plugged into a TV aerial socket, or touches grounded metal, holds the pin down, and esptool ends with `No serial data received`. Unplug the far end of the wire while you flash.

## PAL

### What PAL means here

- **Timing is PAL.** 625 lines, 64 microseconds each, switched on with `-DPAL`. This part came with channel3.
- **There is no PAL color.** The color signal in the tables is NTSC. A PAL color set shows the picture in black and white, a black and white set never cared. With `MONOCHROME` the color signal is left out completely.
- **There is no sound.**
- **The picture is 232 x 264** in the sharp black and white mode that the text uses, and 116 x 264 with 16 colors or grays.
- **It is made for B/G sets**, the standard in most of continental Europe. French SECAM L sets use a different kind of modulation and will not show it. Sets that only have UHF, as many in the UK and Ireland do, cannot tune this low.

### Why 62.5 MHz

Channel E4 officially has its picture carrier at 62.25 MHz. This fork transmits 0.25 MHz above that, on purpose.

Every signal level is a fixed pattern of ones and zeros that repeats along the line. How often it repeats depends on the frequency:

| Frequency | Pattern repeats every | On the TV |
|---|---|---|
| 62.27 MHz, the closest possible to 62.25 | 176 bits | Coarse diagonal stripes over the whole picture |
| 62.5 MHz | 32 bits | Clean |
| 61.25 MHz, US channel 3 | 64 bits | What channel3 uses |

A long pattern beats against the carrier at a low frequency, and that shows as wide stripes. 62.5 MHz is exactly 25/32 of the 80 MHz bit clock, so the pattern is as short as it gets near E4. A TV tunes the quarter megahertz without complaint.

### Changing the channel

The frequency is set in `tablemaker/synthtables.c`:

```c
double MODULATION_Frequency = CHANNEL_E4;
```

Change it, then rebuild the tables and the firmware:

```sh
cd tablemaker && make synthtables && cd ..
make clean ESP_ROOT="$HOME/esp8266" ESP_GCC_VERS=5.2.0 ESPTOOL_PY=esptool.py
make all   ESP_ROOT="$HOME/esp8266" ESP_GCC_VERS=5.2.0 ESPTOOL_PY=esptool.py
```

Rules for picking a frequency:

- It has to be a multiple of 80/1408 MHz (about 0.0568 MHz), so that a whole number of cycles fits into the table.
- Prefer one that is a simple fraction of 80 MHz, for the reason above. In band I those are 47.5, 52.5, 57.5, 62.5 and 67.5 MHz (pattern of 32 bits) and 55 and 65 MHz (16 bits).
- `CHANNEL_3` gives you the original US channel 3 back.

Only 62.5 MHz and 62.27 MHz have been tried on a real TV here.

### Known issue

In PAL the bottom 9 lines of the picture repeat the top 9 lines of the framebuffer. The line counter is 8 bits wide and the PAL picture has 265 lines. The demo screens leave those lines empty, so you do not see it there.

## Troubleshooting

| What you see | What to do |
|---|---|
| `make` does nothing, complains about missing files, or says the modules were not checked out | The submodule is missing. Run `git submodule update --init --recursive`. |
| `bad CPU type in executable` on a Mac | Install Rosetta: `softwareupdate --install-rosetta`. |
| The build stops with `Specify the --chip argument` | You have esptool 5. Install 4.8.1 as in step 1. If you want to keep 5, build with `ESPTOOL_PY="esptool.py --chip esp8266"` instead, that gives the same two files. Flashing with esptool 5 was not tried. |
| You changed `user.cfg` and nothing changed | Run `make clean` before `make all`. |
| No serial port appears when you plug the board in, on a Mac | Install the CH340 driver from step 1: https://www.wch-ic.com/downloads/CH34XSER_MAC_ZIP.html. If macOS asked to allow it, check System Settings under Privacy & Security, then unplug the board and plug it in again. If there is still no port, try another USB cable, many only charge. |
| No serial port appears when you plug the board in, on Linux | Try another USB cable, many only charge. On Ubuntu, the `brltty` package is known to grab these USB serial chips, remove it if you do not need it. |
| `Permission denied` on the port on Linux | Add yourself to the `dialout` group (step 1) and log in again. |
| `No serial data received` | The antenna is holding the RX pin down. Unplug its far end while flashing. See [Antenna](#antenna). |
| Flashing worked, but there is no picture and no WiFi network | Flash again with the long first-time command, including `-fs 4MB`. |
| The web page does not load | `web/page.mpfs` is not on the board. Flash with the long first-time command. |
| Coarse diagonal stripes | The carrier frequency has a long bit pattern. See [Why 62.5 MHz](#why-625-mhz). |
| Text on a gray background instead of black | Turn the brightness of the TV down and the contrast up. If that is not enough, try `WHITE_BORDER`. |
| The picture rolls or bounces | Adjust V-hold on the TV to the middle of the range where the picture stands still. |

## How it works

Everything from here on is the original channel3 README. It describes NTSC and US channel 3. Where it says 61.25 MHz, this fork uses 62.5 MHz.

One demo screen is switched off in this fork: the "38x14 TEXT MODE" intro that came before the framebuffer copy test. Its text did not come out right on the test TV. The list of screens below is adjusted to match.

If you are looking for the kolumbus.fi NTSC/PAL mirror, see it here: https://cnlohr.github.io/channel3/ntsc_pal_frame_documentation/pal_ntsc_from_kolumbus_fi_pami1.html

### Background and RF

This uses the I2S Bus in the same way the esp8266ws2812i2s project does.  Difference is it cranks the output baud to 80 MHz.  We set up DMA buffers and let the CPU fill them as they pass through one line at a time.  The DMA interrupt fills in the buffers one word at a time.  The I2S bus shifts those buffers out at 80 MHz!

You may say "But nyquist says you can't transmit or receive frequencies at more than 1/2 the sample rate (40 MHz in this case).  To a degree that is true.  Some people thought it may be overtones, but what happens in reality something stranger happens.  Everything you transmit is actually mirrored around 1/2 the sample rate (40 MHz).  So, transmitting 60 MHz on an 80 MHz bitclock creates a waveform both at 60 as well as 20.  This isn't perfect.  Some frequencies line up to the 80 MHz well, others do not.

We store a bit pattern in the "premodulated_table" array.  This contains bitstreams for various signals, such as the "sync" level or "colorbust" level, or any of the visual colors.  This table's length of 1408 bits per color was chosen so that when sent out one bit at a time at 80 MHz, it works out to an even multiplier of the NTCS chroma frequency of 315.0/88.0 MHz, or 3.579545455 MHz.  You can calculate this by taking 1408/80MHz = 17.6us * 3.579545 MHz = 63 cycles, exactly.  Conveniently, it also works out to an even multiplier of 61.25 MHz, Channel 3's luma center.  17.6us * 61.25 MHz = 1078 cycles, exactly! When you modulate arbitrary frequencies, sometimes the cycles come out very uneven. 

In order to generate luma (the black and white portion) we modulate 61.25 MHz.  If we generate a strong signal, it is viewed as a very "dark", and a weak signal is a very "bright."  This means when we want to send out a sync pulse, we modulate it as loud as we can... when we want to modulate white, we put out barely any signal at all.  One thing you will notice is dot pour.  This is because the signal we are sending is so terrible.  The chroma signal is very dirty and has a repeating intensity pattern.  While the chroma lines up to the 1408 bit-wide repeating patten, the total number of pixels on the screen does not.  This causes the patterns created to roll down the screen.

In order to generate color, we need to modulate in a chroma signal, 3.579MHz above the baseband.  The chroma is synchronized by a colorburst at the beginning of each line.  This also sets the level for the chroma.  Then, during the line, we can either choose a "color" that has a high coefficient at the chroma level, or a low one.  This determines how vivid the color is.  We can change phase to change the color's hue.

This is basically a 1-bit dithering DAC, operating at a frequency below the nyquist, trying to encode luma and color at the same time.  Don't be surprised that the quality's terrible.

### Code Layout

Tables for handling the line-buffer state machine are (generated/stored?) in MayCbTables.h/c, and similar tables for creating the on-wire signal encoding are in synthtables.c.

Functions to set up the DMA transfers, refill the buffers when they become empty, and change what kind of line should be sent based on the framebuffer contents are in video_broadcast.c. These functions handle all of the modulation.  This sets up the DMA, and an interrupt that is called when the DMA finishes a block (equal to one line).  Upon completion, it uses CbTable to decide what function to call to fill in the line.  The interrupt fills out the next line for DMA which keeps going.

The framebuffer is updated by various demo screens located in user_main.c.

custom_commands.c contain the custom commands used for the NTSC-specific aspects.  Using the common websockets interface there are two added commands.  These include "CO" and "CV" which set the operation mode (CO) and allow users to change the modulation table from a web interface (CV).

### Demo screens

The following demo screens are available.  They normally tick through one after another (except ones after 10), unless the user disables this in the web browser.

### Screen Modes

1. Basic intro screen, shows IP address if available.
2. ESP8266 Features
3. Framebuffer copy test.  Beware, running this screen too long deliberately will cause a crash. <!-- channel3 original: "Intro to and completion of framebuffer copy test."  The intro screen ("38x14 TEXT MODE ...on 232x220 gfx") is commented out in user/user_main.c in this fork, the demo goes straight to the copy test. -->
6. Draw a bunch of lines... IN COLOR!
7. Matrix-based 3D engine demo.
8. Dynamic 3D mesh demo.
9. Pitch for this project's github.
10. Color screen with 16 color balls.
11. 4x4 color swatches, useful for when you're messing with colors in the web GUI.

### Web interface

The web interface is borrowing the web interface from esp8266ws2812i2s.  Power on the ESP, connect to it, then, point your web browser to http://192.168.4.1.  It has a new button "NTSC."  This gives you the option to allow demo to continue from screen to screen, or freeze at a specific screen.  You can specify the screen.  Additionally, for RF testing, you can jam a color.  Whenever the color jam is set to something 0 or above, it turns off all line drawing logic, and simply outputs that color continuously.  This will prevent TV sets from seeing it, however, you can see it on other RF equipment.

It also has an interactive Javascript webworker system that lets you write code to make a new color!  You can create a new bitstream that will be transmitted when a specific color is hit.  You can edit the code and it is effective as you type.  It automatically re-starts the webworker every time you change it.

You should only output -1 or +1 as that is all the ESP can output.  It will then run a DFT with a randomized window over a frequency area you choose.  Increase the DFT window, and it will increase your q (or precision).  Decrease, it decreases your q.  This is to help see how receivers like the TV really understand the signal and help illustrate how wacky this really is.

You can try it in your own browser using this link: http://cnlohr.github.io/channel3/web/page/index.html  Click NTSC and go to town.

### Rawdraw and 3D

For all the 3D and text, I'm using a new modified version of my "rawdraw" library ( http://github.com/cnlohr/rawdraw ) for 3D I'm using fixed point numbers, with 256 as the unit value, and the bottom 8 bits are the fractional component.

### PAL Modification

To allow for PAL broadcasts, the timings in the video_broadcast-library (formerly ntsc_broadcast) were modified. Since I only wanted to use this with a black an white TV, and PAL colour is actually quite complicated to do digitally, I didn't modify the broadcast_tables (synthtables.c). So the library broadcasts a PAL compliant B/W-Signal with NTSC Colour information (kind of like NTSC50).

To enable PAL broadcasting you need to enable ```OPTS += -DPAL``` in user.cfg. 

### Youtube video

Here is the original youtube video on this project:

[![NTSC Video on the ESP8266](http://img.youtube.com/vi/SSiRkpgwVKY/0.jpg)](http://www.youtube.com/watch?v=SSiRkpgwVKY)

Here is the new video (with COLOR):

[![Broadcasting COLOR Channel 3 on an ESP](http://img.youtube.com/vi/bcez5pcp55w/0.jpg)](http://www.youtube.com/watch?v=bcez5pcp55w)
