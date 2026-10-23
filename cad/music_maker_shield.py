"""Adafruit Music Maker MP3 shield, 3 W amp version (product 1788, Rev E board), as a
simple 3D model for checking the case.

Positions come from Adafruit's own board file, Adafruit-Music-Maker-MP3-Shield-RevE.brd in
https://github.com/adafruit/Adafruit-Music-Maker-MP3-Shield-PCB (CC BY-SA, Limor Fried /
Adafruit Industries). Part heights are typical datasheet values, not measured on the board:
check the ones that matter (jack axis height, terminal height) with calipers.

This script and the model it makes are an adaptation of that design, shared under the same
licence, CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0/). Unofficial: not made or
endorsed by Adafruit Industries; "Adafruit" and "Music Maker" are their trademarks.

Coordinates (mm) are the board file's, which are also the Uno's: x from the USB end,
y from the power-header edge, z up from the bottom of the shield's PCB. Components are
on top (+z), the header pins that plug into the Uno point down (-z).

Run:  python music_maker_shield.py   ->  reference/adafruit_music_maker_amp.step
"""
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
OUT = HERE / "reference" / "adafruit_music_maker_amp.step"
# Adafruit's Rev E board file: traces, pads and silkscreen are drawn on the top from it
# (board_art.py), if both are next to this script.
BRD = HERE / "reference" / "boards" / "Adafruit-Music-Maker-MP3-Shield-RevE.brd"

PCB_T = 1.6
# Uno shield outline from the board file (layer 20 of the ARDUINOR3_ICSP footprint).
OUTLINE = [(0, 0), (66.04, 0), (66.04, 2.54), (68.58, 5.08), (68.58, 37.846), (66.04, 40.386),
           (66.04, 51.816), (64.516, 53.34), (0, 53.34)]
HOLES = [(13.97, 2.54), (15.24, 50.80), (66.04, 35.56)]   # 3.2 mm, Uno R3 positions
HOLE_D = 3.2

# 3.5 mm stereo jack X1 (PJ-328 on Rev E; the older v4 board had a 4UCONN 19269 at y 26.162,
# x 0.635-15.135): opening at the USB end, axis along x. Its two locating pegs are at x 4.125
# and 11.125 on the axis (matches mikeoverbay's photo of the back).
JACK_Y = 25.908                    # axis, from the board file
JACK_BODY = (0.625, 15.225, 6.0)   # x0, x1, width (footprint silkscreen)
JACK_H = 5.0                       # body height (typical)
JACK_AXIS_Z = 2.5                  # axis above the PCB top (typical)
JACK_NOSE = (5.0, -1.865)          # nose diameter, and how far it reaches (x)

# Speaker screw terminals (3.5 mm pitch, 2 way), wire entries facing the USB end.
TERMINAL_YS = (17.022, 8.968)      # LEFTSPK, RIGHTSPK centres
TERMINAL_X = (0.2, 7.2)            # body x range (footprint silkscreen, rotated)
TERMINAL_W = 7.0                   # body along y
TERMINAL_H = 9.5                   # body height: matches the case's 24.0 stack height

# Other parts: (name, x centre, y centre, size x, size y, height).
BOXES = [
    ("vs1053", 37.9, 27.1, 7.0, 7.0, 1.4),          # U1, LQFP48
    ("microsd", 9.12, 38.93, 13.25, 14.07, 1.8),    # CN1 socket (silkscreen, rotated)
    ("74hc4050", 21.59, 39.37, 3.9, 9.9, 1.75),     # U5, SOIC16 turned 90
    ("ts2012_amp", 11.871, 12.641, 3.0, 3.0, 0.8),  # U4, WQFN20
    ("regulator", 36.5, 11.7, 1.6, 2.9, 1.1),       # U2, SOT23-6
    ("crystal", 47.9, 26.5, 2.5, 3.2, 0.8),         # Y1
    ("reset_button", 6.223, 50.038, 6.6, 6.0, 3.5), # SW2
]
CAPS = [(20.811, 29.9), (20.811, 24.3)]   # C1, C2: 220 uF electrolytics
CAP_D, CAP_H = 6.3, 7.7

# Male headers into the Uno's sockets: pins along each row (from the board file).
HEADER_ROWS = [
    (2.54, [27.94 + 2.54 * i for i in range(8)]),                 # power
    (2.54, [50.8 + 2.54 * i for i in range(6)]),                  # analog
    (50.8, [18.796 + 2.54 * i for i in range(10)]),               # SCL ... D8
    (50.8, [45.72 + 2.54 * i for i in range(8)]),                 # D7 ... D0
]
HEADER_PLASTIC = 2.5   # spacer under the shield
PIN_BELOW = 6.0        # pin length below the spacer
PIN = 0.64


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def pcb():
    board = cq.Workplane("XY").polyline(OUTLINE).close().extrude(PCB_T).val()
    for x, y in HOLES:
        board = board.cut(cq.Solid.makeCylinder(HOLE_D / 2, PCB_T + 2, cq.Vector(x, y, -1)))
    return board


def jack():
    x0, x1, w = JACK_BODY
    body = box(x0, x1, JACK_Y - w / 2, JACK_Y + w / 2, PCB_T, PCB_T + JACK_H)
    nose_d, nose_x = JACK_NOSE
    nose = cq.Solid.makeCylinder(nose_d / 2, x0 - nose_x + 0.5,
                                 cq.Vector(x0 + 0.5, JACK_Y, PCB_T + JACK_AXIS_Z), cq.Vector(-1, 0, 0))
    return body.fuse(nose)


def terminals():
    return [box(*TERMINAL_X, y - TERMINAL_W / 2, y + TERMINAL_W / 2, PCB_T, PCB_T + TERMINAL_H)
            for y in TERMINAL_YS]


def parts():
    out = [box(x - sx / 2, x + sx / 2, y - sy / 2, y + sy / 2, PCB_T, PCB_T + h)
           for _, x, y, sx, sy, h in BOXES]
    out += [cq.Solid.makeCylinder(CAP_D / 2, CAP_H, cq.Vector(x, y, PCB_T)) for x, y in CAPS]
    return out


def headers():
    """(plastic strips, pins)"""
    plastic, pins = [], []
    for y, xs in HEADER_ROWS:
        plastic.append(box(xs[0] - 1.27, xs[-1] + 1.27, y - 1.27, y + 1.27, -HEADER_PLASTIC, 0))
        pins += [box(x - PIN / 2, x + PIN / 2, y - PIN / 2, y + PIN / 2,
                     -HEADER_PLASTIC - PIN_BELOW, PCB_T + 1.0) for x in xs]
    return plastic, pins


# Colours, roughly as on the real board (Adafruit's product photo).
SOLDERMASK = cq.Color(0.06, 0.30, 0.78)   # Adafruit blue
TRACE = cq.Color(0.12, 0.40, 0.90)        # copper under the mask, a shade lighter
BLACK = cq.Color(0.07, 0.07, 0.08)
TERMINAL_GREEN = cq.Color(0.42, 0.78, 0.58)   # Rev E ships with green terminals soldered on
STEEL = cq.Color(0.74, 0.75, 0.78)
CAP = cq.Color(0.88, 0.88, 0.90)          # silver-white can
GOLD = cq.Color(0.83, 0.66, 0.22)
PART_COLOURS = {"vs1053": BLACK, "microsd": STEEL, "74hc4050": BLACK, "ts2012_amp": BLACK,
                "regulator": BLACK, "crystal": STEEL, "reset_button": STEEL}


def shield_assembly():
    """cq.Assembly in board coordinates, coloured roughly like the real board."""
    a = cq.Assembly(name="music_maker_amp")
    a.add(pcb(), name="pcb", color=SOLDERMASK)
    try:
        import board_art as ba
    except ImportError:
        ba = None
    if ba is not None and BRD.exists():
        colours = dict(ba.COLOURS, copper=(TRACE.toTuple()[:3]))
        for layer, solid in ba.art_solids(ba.board_art(str(BRD)), PCB_T).items():
            a.add(solid, name=f"art_{layer}", color=cq.Color(*colours[layer]))
    a.add(jack(), name="jack_3_5mm", color=BLACK)
    for i, t in enumerate(terminals()):
        a.add(t, name=f"speaker_terminal_{'LR'[i]}", color=TERMINAL_GREEN)
    for (name, *_), p in zip(BOXES + [("cap_c1",), ("cap_c2",)], parts()):
        a.add(p, name=name, color=CAP if name.startswith("cap") else PART_COLOURS[name])
    plastic, pins = headers()
    for i, h in enumerate(plastic):
        a.add(h, name=f"header_plastic_{i}", color=BLACK)
    a.add(cq.Compound.makeCompound(pins), name="header_pins", color=GOLD)
    return a


def shield_solid():
    """Everything fused into one compound, for placing in the case assembly."""
    plastic, pins = headers()
    return cq.Compound.makeCompound([pcb(), jack(), *terminals(), *parts(), *plastic, *pins])


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    shield_assembly().export(str(OUT))
    print("wrote", OUT)
    print(f"jack axis: y {JACK_Y}, {PCB_T + JACK_AXIS_Z:.1f} above the shield's PCB bottom, "
          f"nose to x {JACK_NOSE[1]}")
