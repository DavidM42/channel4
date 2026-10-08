#!/usr/bin/env python3
"""Draws the surface-mount TV shield for the Wemos D1 Mini as a KiCad board.

It is the same circuit as ../tv-shield, with parts that an assembly service places by machine.

Run it with the Python that comes with KiCad 9 (it needs the pcbnew module and KiCad's footprint libraries):
    python3 make_board.py tv-shield-smd.kicad_pcb

Next to the board it writes the two lists an assembly service asks for: tv-shield-smd-bom.csv (the parts) and
tv-shield-smd-positions.csv (where they go).

The board is looked at from the top, with the antenna end of the D1 Mini at the top and its USB socket at the bottom.
All positions are in millimeters from the top left corner.
"""
import csv
import os
import sys
import pcbnew
from pcbnew import FromMM, VECTOR2I

LIBS = "/usr/share/kicad/footprints/"
W, H = 25.6, 25.6                  # as wide as a D1 Mini, and square
ROW_L, ROW_R = 1.37, 24.23         # the two pin rows, 22.86 mm apart
PIN1_Y, PITCH = 2.0, 2.54
LEFT = ["RST", "A0", "D0", "D5", "D6", "D7", "D8", "3V3"]   # antenna end first
RIGHT = ["TX", "RX", "D1", "D2", "D3", "D4", "GND", "5V"]

# The parts to buy.  The column names are the ones JLCPCB reads, other services take the same file.
# The LCSC numbers were looked up in JLCPCB's parts list.  The pin rows are in neither list.  They are left to you:
# they are through-hole, which way round they go depends on how you stack the boards, and a D1 Mini comes with them.
# A part that is in this list but not in the positions file makes JLCPCB stop with "designators don't exist in the
# CPL file".
PARTS = {
    "R3": ("100R", "Resistor, 100 ohm, 0603, 1 %", "0603", "UNI-ROYAL", "0603WAF1000T5E", "C22775"),
    "R1": ("2k2", "Resistor, 2.2 kohm, 0603, 1 %", "0603", "UNI-ROYAL", "0603WAF2201T5E", "C4190"),
    "R2": ("75R", "Resistor, 75 ohm, 0603, 1 %", "0603", "UNI-ROYAL", "0603WAF750JT5E", "C4275"),
    "C2": ("10p", "Ceramic capacitor, 10 pF, 50 V, C0G, 0603", "0603", "Samsung", "CL10C100JB8NNNC", "C1634"),
    "C1": ("1u", "Ceramic capacitor, 1 uF, 50 V, X5R, 0603", "0603", "Samsung", "CL10A105KB8NNNC", "C15849"),
    "J3": ("3.5 mm socket", "3.5 mm socket, 4 contacts, surface-mount", "PJ-320D", "SHOU HAN", "PJ-320D",
           "C431535"),
}

board = pcbnew.BOARD()


def P(x, y):
    return VECTOR2I(FromMM(x), FromMM(y))


def net(name):
    n = pcbnew.NETINFO_ITEM(board, name)
    board.Add(n)
    return n


RX, FIL, MID, OUT, GND = net("RX"), net("FILTERED"), net("MID"), net("TV"), net("GND")


def place(lib, name, ref, value, x, y, angle=0, silk=True):
    fp = pcbnew.FootprintLoad(LIBS + lib + ".pretty", name)
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    fp.SetPosition(P(x, y))
    fp.SetOrientationDegrees(angle)
    # The printed outline of a library part goes to a layer that is not made if it is not wanted (silk=False),
    # and so does every line of it that would be printed over the edge of the board.
    for g in list(fp.GraphicalItems()):
        box = g.GetBoundingBox()
        if g.GetLayer() == pcbnew.F_SilkS and (
                not silk or box.GetLeft() < FromMM(0.3) or box.GetTop() < FromMM(0.3)
                or box.GetRight() > FromMM(W - 0.3) or box.GetBottom() > FromMM(H - 0.3)):
            g.SetLayer(pcbnew.Cmts_User)
    board.Add(fp)
    return fp


def connect(fp, nets):
    for pad in fp.Pads():
        if pad.GetNumber() in nets:
            pad.SetNet(nets[pad.GetNumber()])


def at(fp, number):
    """Where a pad of a placed part is, in millimeters."""
    for pad in fp.Pads():
        if pad.GetNumber() == number:
            return pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y)


def track(n, points, width=0.5):
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(P(x1, y1))
        t.SetEnd(P(x2, y2))
        t.SetWidth(FromMM(width))
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(n)
        board.Add(t)


def via(x, y):
    """Joins the ground areas of the two sides."""
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(P(x, y))
    v.SetDrill(FromMM(0.4))
    v.SetWidth(pcbnew.F_Cu, FromMM(0.8))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(GND)
    board.Add(v)


def text(s, x, y, size=0.8, align="center", layer=pcbnew.F_SilkS):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(P(x, y))
    t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size)))
    t.SetTextThickness(FromMM(max(0.12, size * 0.15)))
    t.SetHorizJustify({"left": pcbnew.GR_TEXT_H_ALIGN_LEFT, "right": pcbnew.GR_TEXT_H_ALIGN_RIGHT,
                       "center": pcbnew.GR_TEXT_H_ALIGN_CENTER}[align])
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    board.Add(t)


def round_pad(fp, number, x, y, n, size=1.8, drill=1.0):
    pad = pcbnew.PAD(fp)
    pad.SetNumber(number)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    pad.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(pcbnew.F_Cu, VECTOR2I(FromMM(size), FromMM(size)))
    pad.SetDrillSize(VECTOR2I(FromMM(drill), FromMM(drill)))
    pad.SetLayerSet(pad.PTHMask())
    pad.SetPosition(P(x, y))
    pad.SetNet(n)
    fp.Add(pad)
    return pad


def ground(layer):
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNet(GND)
    outline = zone.Outline()
    outline.NewOutline()
    for x, y in [(0, 0), (W, 0), (W, H), (0, H)]:
        outline.Append(FromMM(x), FromMM(y))
    zone.SetLocalClearance(FromMM(0.3))
    zone.SetMinThickness(FromMM(0.25))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    zone.SetThermalReliefGap(FromMM(0.3))
    zone.SetThermalReliefSpokeWidth(FromMM(0.5))
    board.Add(zone)


# Outline
edge = pcbnew.PCB_SHAPE(board)
edge.SetShape(pcbnew.SHAPE_T_RECT)
edge.SetStart(P(0, 0))
edge.SetEnd(P(W, H))
edge.SetLayer(pcbnew.Edge_Cuts)
edge.SetWidth(FromMM(0.1))
board.Add(edge)

# The two pin rows of the D1 Mini.  These stay through-hole.
left = place("Connector_PinHeader_2.54mm", "PinHeader_1x08_P2.54mm_Vertical", "J1", "D1 Mini left row", ROW_L, PIN1_Y,
             silk=False)
right = place("Connector_PinHeader_2.54mm", "PinHeader_1x08_P2.54mm_Vertical", "J2", "D1 Mini right row", ROW_R, PIN1_Y,
              silk=False)
connect(right, {str(RIGHT.index("RX") + 1): RX, str(RIGHT.index("GND") + 1): GND})
RX_Y = PIN1_Y + PITCH * RIGHT.index("RX")
for i in range(8):
    y = PIN1_Y + PITCH * i
    text(LEFT[i], ROW_L + 1.3, y, 0.8, "left")
    text(RIGHT[i], ROW_R - 1.3, y, 0.8, "right")

# The parts sit in a line that starts at the RX pin.  The two that go to ground hang below it.
RES = ("Resistor_SMD", "R_0603_1608Metric_Pad0.98x0.95mm_HandSolder")
CAP = ("Capacitor_SMD", "C_0603_1608Metric_Pad1.08x0.95mm_HandSolder")
LOW_Y = RX_Y + 2.5
r3 = place(*RES, "R3", "100R", 19.0, RX_Y, 180)      # R3 and C2: the filter at the pin from the main README
connect(r3, {"1": RX, "2": FIL})
c2 = place(*CAP, "C2", "10p", 17.2, LOW_Y, 270)
connect(c2, {"1": FIL, "2": GND})
r1 = place(*RES, "R1", "2k2", 15.4, RX_Y, 180)       # R1: takes the signal down to what a TV input expects
connect(r1, {"1": FIL, "2": MID})
r2 = place(*RES, "R2", "75R", 13.6, LOW_Y, 270)  # R2: from behind R1 to ground
connect(r2, {"1": MID, "2": GND})
c1 = place(*CAP, "C1", "1u", 11.8, RX_Y, 180)      # C1: in series to the TV
connect(c1, {"1": MID, "2": OUT})

# J3: 3.5 mm socket PJ-320D, turned so that its opening is at the bottom edge.  It has four contacts.  Only the tip
# carries the signal.  The other three go to ground: the sleeve of a plug with two or three contacts covers them.
JX, JY = 12.8, H - 6.22
jack = place("Connector_Audio", "Jack_3.5mm_PJ320D_Horizontal", "J3", "PJ-320D", JX, JY, 90, silk=False)
connect(jack, {"T": OUT, "R1": GND, "R2": GND, "S": GND})

# J4: two holes for a cable that is soldered on instead of the socket
pads = pcbnew.FOOTPRINT(board)
pads.SetReference("J4")
pads.SetValue("cable")
pads.Reference().SetVisible(False)
pads.Value().SetVisible(False)
pads.SetExcludedFromBOM(True)
pads.SetExcludedFromPosFiles(True)
pads.SetPosition(P(2.7, 22.9))
board.Add(pads)
round_pad(pads, "1", 2.7, 22.9, OUT, 2.0, 1.1)
round_pad(pads, "2", 5.5, 22.9, GND, 2.0, 1.1)

# Tracks on the top.  Both sides are ground everywhere else.
tip_x, tip_y = at(jack, "T")
track(RX, [(ROW_R, RX_Y), at(r3, "1")])
track(FIL, [at(r3, "2"), at(r1, "1")])
track(FIL, [(17.2, RX_Y), at(c2, "1")])
track(MID, [at(r1, "2"), at(c1, "1")])
track(MID, [(13.6, RX_Y), at(r2, "1")])
track(OUT, [at(c1, "2"), (7.0, RX_Y), (7.0, tip_y), (tip_x, tip_y)])
track(OUT, [(7.0, tip_y), (5.6, tip_y + 1.4), (5.6, 20.0), (2.7, 22.9)])
ground(pcbnew.F_Cu)
ground(pcbnew.B_Cu)
# Vias join the two ground areas: one between the two parts that go to ground, the rest spread over the board.
for x, y in [(15.4, LOW_Y + 1.3), (20.5, 12.0), (20.5, 21.5), (5.9, 12.0), (18.5, 15.5), (18.5, 19.5)]:
    via(x, y)

# Labels
text("WIFI ANTENNA THIS END", W / 2, 1.2, 0.8)
text("100R", 19.0, RX_Y - 1.45, 0.8)
text("2k2", 15.4, RX_Y - 1.45, 0.8)
text("1u", 11.8, RX_Y - 1.45, 0.8)
text("10p", 17.2, LOW_Y + 2.4, 0.8)
text("75R", 13.6, LOW_Y + 2.4, 0.8)
text("PJ-320D", JX, JY + 1.65, 0.8)
text("TV", 21.0, 23.6, 1.2)
text("TV", 2.3, 24.6, 0.8)
text("GND", 5.6, 24.6, 0.8)
text("channel4 TV shield", W / 2, 1.7, 1.0, layer=pcbnew.B_SilkS)
text("SMD", W / 2, 3.6, 1.0, layer=pcbnew.B_SilkS)
text("RX-100R-2k2-1u-TV", W / 2, 9.0, 0.8, layer=pcbnew.B_SilkS)
text("10p, 75R to GND", W / 2, 10.6, 0.8, layer=pcbnew.B_SilkS)

pcbnew.SaveBoard(sys.argv[1], board)

# The lists for an assembly service
folder = os.path.dirname(os.path.abspath(sys.argv[1]))
with open(os.path.join(folder, "tv-shield-smd-bom.csv"), "w", newline="") as f:
    out = csv.writer(f)
    out.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Quantity", "Description", "Manufacturer",
                  "Manufacturer Part #"])
    rows = {}
    for ref, (value, description, size, maker, part, lcsc) in PARTS.items():
        rows.setdefault((value, size, lcsc, description, maker, part), []).append(ref)
    for (value, size, lcsc, description, maker, part), refs in rows.items():
        out.writerow([value, ",".join(refs), size, lcsc, len(refs), description, maker, part])
with open(os.path.join(folder, "tv-shield-smd-positions.csv"), "w", newline="") as f:
    out = csv.writer(f)
    out.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in PARTS:
            # Y counts upwards here, as in the Gerber files.
            out.writerow([ref, "%.2f" % pcbnew.ToMM(fp.GetPosition().x), "%.2f" % -pcbnew.ToMM(fp.GetPosition().y),
                          "Top", "%g" % fp.GetOrientationDegrees()])

# Fill the ground areas.  On a board that was just built in memory the zone filler crashes, on a loaded one it works.
board = pcbnew.LoadBoard(sys.argv[1])
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(sys.argv[1], board)
