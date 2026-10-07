#!/usr/bin/env python3
"""Draws the TV shield for the Wemos D1 Mini as a KiCad board.

Run it with the Python that comes with KiCad 9 (it needs the pcbnew module and KiCad's footprint libraries):
    python3 make_board.py tv-shield.kicad_pcb

The board is looked at from the top, with the antenna end of the D1 Mini at the top and its USB socket at the bottom.
All positions are in millimeters from the top left corner.
"""
import sys
import pcbnew
from pcbnew import FromMM, VECTOR2I

LIBS = "/usr/share/kicad/footprints/"
W, H = 25.6, 25.6                  # as wide as a D1 Mini, and square
ROW_L, ROW_R = 1.37, 24.23         # the two pin rows, 22.86 mm apart
PIN1_Y, PITCH = 2.0, 2.54
LEFT = ["RST", "A0", "D0", "D5", "D6", "D7", "D8", "3V3"]   # antenna end first
RIGHT = ["TX", "RX", "D1", "D2", "D3", "D4", "GND", "5V"]

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


def track(n, points, width=0.5):
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(P(x1, y1))
        t.SetEnd(P(x2, y2))
        t.SetWidth(FromMM(width))
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(n)
        board.Add(t)


def text(s, x, y, size=0.8, align="center", layer=pcbnew.F_SilkS, angle=0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(P(x, y))
    t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size)))
    t.SetTextThickness(FromMM(max(0.12, size * 0.15)))
    t.SetHorizJustify({"left": pcbnew.GR_TEXT_H_ALIGN_LEFT, "right": pcbnew.GR_TEXT_H_ALIGN_RIGHT,
                       "center": pcbnew.GR_TEXT_H_ALIGN_CENTER}[align])
    t.SetTextAngleDegrees(angle)
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


def outline(points):
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        e = pcbnew.PCB_SHAPE(board)
        e.SetShape(pcbnew.SHAPE_T_SEGMENT)
        e.SetStart(P(x1, y1))
        e.SetEnd(P(x2, y2))
        e.SetLayer(pcbnew.Edge_Cuts)
        e.SetWidth(FromMM(0.1))
        board.Add(e)

# The two pin rows of the D1 Mini
left = place("Connector_PinHeader_2.54mm", "PinHeader_1x08_P2.54mm_Vertical", "J1", "D1 Mini left row", ROW_L, PIN1_Y, silk=False)
right = place("Connector_PinHeader_2.54mm", "PinHeader_1x08_P2.54mm_Vertical", "J2", "D1 Mini right row", ROW_R, PIN1_Y, silk=False)
connect(right, {str(RIGHT.index("RX") + 1): RX, str(RIGHT.index("GND") + 1): GND})
RX_Y = PIN1_Y + PITCH * RIGHT.index("RX")
for i in range(8):
    y = PIN1_Y + PITCH * i
    text(LEFT[i], ROW_L + 1.3, y, 0.8, "left")
    text(RIGHT[i], ROW_R - 1.3, y, 0.8, "right")

# Three resistors lie in rows on the right, the two capacitors stand on the left.
ROW_A, ROW_B, ROW_C = RX_Y, RX_Y + 3.1, RX_Y + 6.2
RES = "R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
RES_L, RES_R = 11.98, 19.6

# R3 and C2: the filter at the pin from the main README.  R3 starts right next to the RX pin, so that the wire
# that carries the full signal is as short as it can be.  C2 goes to ground behind it.
r3 = place("Resistor_THT", RES, "R3", "100R", RES_R, ROW_A, 180)
connect(r3, {"1": RX, "2": FIL})
c2 = place("Capacitor_THT", "C_Disc_D3.0mm_W1.6mm_P2.50mm", "C2", "10p", 9.44, ROW_A, 180)
connect(c2, {"1": FIL, "2": GND})
# R1: takes the signal down to what a TV input expects
r1 = place("Resistor_THT", RES, "R1", "2k2", RES_L, ROW_B)
connect(r1, {"1": FIL, "2": MID})
# R2: from behind R1 to ground
r2 = place("Resistor_THT", RES, "R2", "75R", RES_R, ROW_C, 180)
connect(r2, {"1": MID, "2": GND})
# C1: in series to the TV.  5 mm between the outer holes, and a third hole for parts with 2.5 mm between their legs.
C1_X, C1_Y = 8.2, 7.1
c1 = place("Capacitor_THT", "C_Disc_D5.0mm_W2.5mm_P5.00mm", "C1", "1n to 1u", C1_X, C1_Y, 270)
connect(c1, {"1": MID, "2": OUT})
round_pad(c1, "2", C1_X, C1_Y + 2.5, OUT, 1.6, 0.8)

# J3: 3.5 mm socket, CUI SJ1-3523N, its opening at the bottom edge.  Round holes instead of the slots of the
# library part, which not every board maker drills.  The part brings the piece of board edge it sits on with it,
# with a notch for its collar, 4.5 mm below its middle.  The rest of the outline joins it on both sides.
JX, JY = 12.8, H - 4.5
jack = place("Connector_Audio", "Jack_3.5mm_CUI_SJ1-3523N_Horizontal", "J3", "SJ1-3523N", JX, JY, silk=False)
outline([(JX - 6.5, H), (0, H), (0, 0), (W, 0), (W, H), (JX + 6.5, H)])
for pad in jack.Pads():
    if pad.GetNumber() in ("T", "R", "S"):
        pad.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetSize(pcbnew.F_Cu, VECTOR2I(FromMM(2.4), FromMM(2.4)))
        pad.SetDrillShape(pcbnew.PAD_DRILL_SHAPE_CIRCLE)
        pad.SetDrillSize(VECTOR2I(FromMM(1.5), FromMM(1.5)))
# The ring goes to ground as well: a mono plug shorts it to the sleeve anyway.
connect(jack, {"T": OUT, "S": GND, "R": GND})

# J4: two holes for a cable that is soldered on instead of the socket
pads = pcbnew.FOOTPRINT(board)
pads.SetReference("J4")
pads.SetValue("cable")
pads.Reference().SetVisible(False)
pads.Value().SetVisible(False)
pads.SetPosition(P(2.7, 22.9))
board.Add(pads)
round_pad(pads, "1", 2.7, 22.9, OUT, 2.0, 1.1)
round_pad(pads, "2", 5.5, 22.9, GND, 2.0, 1.1)

# Tracks, all on the top.  The bottom is one ground area.
TRUNK_Y = 12.4
track(RX, [(ROW_R, RX_Y), (RES_R, ROW_A)])
track(FIL, [(9.44, ROW_A), (RES_L, ROW_A), (RES_L, ROW_B)])
track(MID, [(RES_R, ROW_B), (RES_R, ROW_C)])
track(MID, [(RES_R, ROW_B + 1.55), (10.2, ROW_B + 1.55), (10.2, C1_Y), (C1_X, C1_Y)])
track(OUT, [(C1_X, C1_Y + 2.5), (C1_X, TRUNK_Y)])
track(OUT, [(5.6, TRUNK_Y), (JX + 5.0, TRUNK_Y), (JX + 5.0, JY - 5.0)])
track(OUT, [(5.6, TRUNK_Y), (5.6, 20.4), (3.1, 22.9), (2.7, 22.9)])

zone = pcbnew.ZONE(board)
zone.SetLayer(pcbnew.B_Cu)
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

# Labels
text("WIFI ANTENNA THIS END", W / 2, 1.2, 0.8)
text("100R", 15.8, ROW_A, 1.0)
text("2k2", 15.8, ROW_B, 1.0)
text("75R", 15.8, ROW_C, 1.0)
text("10p", 8.2, 2.55, 0.8)
text("C1", 6.9, C1_Y + 1.5, 0.8, "right")
text("+", 6.9, C1_Y - 0.1, 1.0, "right")
text("TV", 21.0, 23.6, 1.2)
text("SJ1-3523N", JX, JY - 2.7, 0.8)
text("TV", 2.3, 24.6, 0.8)
text("GND", 5.6, 24.6, 0.8)
text("channel4 TV shield", W / 2, 1.7, 1.0, layer=pcbnew.B_SilkS)
text("RX-100R-2k2-C1-TV", W / 2, 13.9, 0.8, layer=pcbnew.B_SilkS)
text("10p, 75R to GND", W / 2, 18.6, 0.8, layer=pcbnew.B_SilkS)

pcbnew.SaveBoard(sys.argv[1], board)

# Fill the ground area.  On a board that was just built in memory the zone filler crashes, on a loaded one it works.
board = pcbnew.LoadBoard(sys.argv[1])
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(sys.argv[1], board)
