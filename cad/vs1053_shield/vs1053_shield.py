"""Model of the HW-261 "VS1053 MP3 Shield" (red board, two 3.5 mm jacks, mic, microSD) for the
drum-amp MP3 player.

Measured from the product photos mikeoverbay sent (2026-10-21), scaled on the Arduino header
sockets (16.46 px/mm). The header pins are on the standard Uno grid, so the shield plugs onto the
Uno model exactly. Everything else comes from the photo and is good to about +-1 mm. Two photos
agree on two quirks of this board:
  - its mounting holes are not on the Uno's hole positions;
  - the board sits about 1.2 mm toward the digital-pin side of the Uno.
The two jacks face the Uno's far end, the end opposite its USB socket.

Coordinates (mm), as in Arduino's Uno drawing: X from the Uno's USB end, Y from its power-header
edge, Z = 0 at the bottom of the shield's PCB, parts on top. On an Uno, the shield's PCB bottom
sits STACK_GAP above the Uno's PCB top (yellow spacers resting on the Uno's sockets).

Outputs (next to this script):
  vs1053_hw261_shield.step  - the shield alone, coloured parts
  uno_vs1053_stack.step     - mikeoverbay's Uno model with the shield plugged on

Run:  python vs1053_shield.py
"""
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
UNO_STEP = HERE.parent / "reference" / "arduino_uno_r3.step"
UNO_MODEL_XY = (33.04, 27.26)     # Uno model x, y + this = Uno coordinates (matched on its 4 holes)
UNO_MODEL_PCB_T = 1.4             # that model's board thickness

PCB_T = 1.6
STACK_GAP = 11.0                  # Uno PCB top to shield PCB bottom: 8.5 sockets + 2.5 spacers
SOCKET_H = 8.5                    # female stacking sockets on top
SPACER_H, PIN_BELOW = 2.5, 10.5   # yellow spacers under the board, pins reach this far below it
HOLE_D = 3.2

# Board outline (X, Y), anticlockwise from the top view. Cut back at the USB end to clear the
# Uno's USB socket, with a step and 45 degree edge over its power jack. At the far end the middle
# sticks out round the jacks.
OUTLINE = [
    (17.47, 1.42), (65.52, 1.42), (65.52, 5.97), (67.77, 8.22), (67.77, 38.53), (65.52, 41.0),
    (65.52, 54.39), (10.85, 54.39), (10.85, 20.25), (17.47, 13.87),
]
HOLES = [(16.9, 52.1), (65.5, 37.7)]

# Header pins (X along the board, Y row): power RST..VIN, analog A0..A5 at Y 2.54;
# digital AREF, GND, D13..D8 and D7..D0 at Y 50.8 (R2-style headers, no SDA/SCL).
HEADERS = {
    "power": ([33.02 + 2.54 * i for i in range(6)], 2.54, (0.85, 0.15, 0.15)),
    "analog": ([50.80 + 2.54 * i for i in range(6)], 2.54, (0.25, 0.55, 0.90)),
    "digital_8_13": ([23.88 + 2.54 * i for i in range(8)], 50.8, (0.85, 0.15, 0.15)),
    "digital_0_7": ([45.72 + 2.54 * i for i in range(8)], 50.8, (0.25, 0.55, 0.90)),
}

BLACK, SILVER, GOLD = (0.08, 0.08, 0.08), (0.75, 0.75, 0.78), (0.85, 0.75, 0.2)
PCB_RED, YELLOW = (0.80, 0.08, 0.08), (0.95, 0.80, 0.15)

# Parts on top: name -> (X centre, Y centre, size X, size Y, height, colour)
PARTS = {
    "microSD socket": (17.93, 37.93, 14.5, 15.5, 1.9, SILVER),    # card goes in from the USB end
    "VS1053": (42.6, 24.5, 9.0, 9.0, 1.4, BLACK),                 # 7 x 7 LQFP-48 plus leads
    "regulator 3V3": (27.86, 9.86, 6.5, 7.0, 1.8, BLACK),         # AMS1117 SOT-223
    "regulator 1V8": (27.86, 21.0, 6.5, 7.0, 1.8, BLACK),
    "reset button": (16.6, 24.1, 6.0, 6.0, 3.5, BLACK),
}
CRYSTAL = (42.7, 33.9, 10.5, 4.6, 3.6)        # HC-49S, long side along X
MIC = (61.2, 42.8, 6.0, 5.0)                   # electret capsule: X, Y, diameter, height
# 3.5 mm jacks: Y centre, body X from..to, barrel front X; body 6.2 wide x 5 tall
JACKS = {"headphone out": 13.69, "mic in": 24.41}
JACK_BODY_X, JACK_FRONT_X, JACK_W, JACK_H = (57.14, 68.08), 70.93, 6.2, 5.0


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def board():
    b = cq.Workplane("XY").polyline(OUTLINE).close().extrude(PCB_T)
    b = b.edges("|Z").edges(cq.selectors.NearestToPointSelector((10.85, 54.39, PCB_T / 2))).fillet(2.0)
    for x, y in HOLES:
        b = b.cut(cq.Workplane("XY").center(x, y).circle(HOLE_D / 2).extrude(PCB_T))
    return b.val()


def jack(y):
    """3.5 mm socket lying on the board, opening toward +X (the Uno's far end)."""
    z0 = PCB_T
    body = box(JACK_BODY_X[0], JACK_BODY_X[1], y - JACK_W / 2, y + JACK_W / 2, z0, z0 + JACK_H)
    barrel = cq.Solid.makeCylinder(2.9, JACK_FRONT_X - JACK_BODY_X[1] + 0.01,
                                   cq.Vector(JACK_BODY_X[1] - 0.01, y, z0 + JACK_H / 2), cq.Vector(1, 0, 0))
    hole = cq.Solid.makeCylinder(1.8, 14.0, cq.Vector(JACK_FRONT_X + 0.1, y, z0 + JACK_H / 2), cq.Vector(-1, 0, 0))
    return body.fuse(barrel).cut(hole)


def shield_parts():
    """{name: (solid, colour)} with the PCB bottom at Z = 0."""
    parts = {"pcb": (board(), PCB_RED)}
    for name, (x, y, sx, sy, h, col) in PARTS.items():
        parts[name] = (box(x - sx / 2, x + sx / 2, y - sy / 2, y + sy / 2, PCB_T, PCB_T + h), col)
    # Reset button cap
    x, y = PARTS["reset button"][:2]
    parts["reset cap"] = (cq.Solid.makeCylinder(1.75, 1.5, cq.Vector(x, y, PCB_T + 3.5)), BLACK)
    cx, cy, cl, cw, ch = CRYSTAL
    xtal = (cq.Workplane("XY", origin=(cx, cy, PCB_T)).sketch().slot(cl - cw, cw, angle=0).finalize()
            .extrude(ch).val())
    parts["crystal 12.288 MHz"] = (xtal, SILVER)
    mx, my, md, mh = MIC
    parts["microphone"] = (cq.Solid.makeCylinder(md / 2, mh, cq.Vector(mx, my, PCB_T)), SILVER)
    for name, y in JACKS.items():
        parts[f"jack {name}"] = (jack(y), BLACK)
    for name, (xs, y, col) in HEADERS.items():
        x0, x1 = xs[0] - 1.27, xs[-1] + 1.27
        sock = box(x0, x1, y - 1.27, y + 1.27, PCB_T, PCB_T + SOCKET_H)
        for x in xs:                                            # socket openings
            sock = sock.cut(box(x - 0.45, x + 0.45, y - 0.45, y + 0.45, PCB_T + 2.0, PCB_T + SOCKET_H + 1))
        parts[f"socket {name}"] = (sock, col)
        parts[f"spacer {name}"] = (box(x0, x1, y - 1.27, y + 1.27, -SPACER_H, 0), YELLOW)
        pins = [box(x - 0.32, x + 0.32, y - 0.32, y + 0.32, -PIN_BELOW, 0) for x in xs]
        parts[f"pins {name}"] = (cq.Compound.makeCompound(pins), GOLD)
    return parts


def uno_model():
    """mikeoverbay's Uno model in Uno coordinates (PCB bottom at Z = 0), or None."""
    if not UNO_STEP.exists():
        return None
    ox, oy = UNO_MODEL_XY
    return cq.importers.importStep(str(UNO_STEP)).val().moved(cq.Location(cq.Vector(ox, oy, 0)))


def assembly(parts, name, dz=0.0):
    assy = cq.Assembly(name=name)
    for n, (solid, col) in parts.items():
        assy.add(solid.moved(cq.Location(cq.Vector(0, 0, dz))), name=n.replace(" ", "_"), color=cq.Color(*col))
    return assy


if __name__ == "__main__":
    parts = shield_parts()
    assembly(parts, "vs1053_hw261_shield").export(str(HERE / "vs1053_hw261_shield.step"))
    uno = uno_model()
    if uno is not None:
        stack = cq.Assembly(name="uno_vs1053_stack")
        stack.add(uno, name="arduino_uno", color=cq.Color(0.1, 0.35, 0.6))
        stack.add(assembly(parts, "vs1053_shield", dz=UNO_MODEL_PCB_T + STACK_GAP), name="vs1053_shield")
        stack.export(str(HERE / "uno_vs1053_stack.step"))
    b = cq.Compound.makeCompound([s for s, _ in parts.values()]).BoundingBox()
    print(f"shield overall X {b.xmin:.2f}..{b.xmax:.2f}  Y {b.ymin:.2f}..{b.ymax:.2f}  Z {b.zmin:.2f}..{b.zmax:.2f}")
    print(f"stacked on the Uno: shield PCB bottom {UNO_MODEL_PCB_T + STACK_GAP:.2f} above the Uno PCB bottom")
