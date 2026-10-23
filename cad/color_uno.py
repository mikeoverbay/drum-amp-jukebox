"""Colour mikeoverbay's Arduino Uno STEP model (one fused solid, no colours) by face, so it
looks like the real board next to the coloured Music Maker model.

STEP can carry colours per face (but no textures). Faces are sorted by where they are:
  - the PCB slab (z 0 to 1.4)      -> Arduino teal
  - the USB-B socket region         -> steel
  - the power jack region           -> black
  - the crystal and reset button    -> silver / steel
  - round faces 2.5 to 4.5 mm radius (the electrolytic caps) -> silver
  - everything else on top          -> black (headers, power jack, chips, button)
Model coordinates = Uno coordinates - (33.04, 27.26); Uno x from the USB end, y from the
power-header edge.

Run:  python color_uno.py   ->  reference/arduino_uno_r3_coloured.step
"""
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
SRC = HERE / "reference" / "arduino_uno_r3.step"
FIXED = Path.home() / "OneDrive" / "Desktop" / "STEP files" / "ARDUINO UNO R3 Step - fixed to Arduino drawing.STEP"
OUT = HERE / "reference" / "arduino_uno_r3_coloured.step"   # board artwork: see decals/
# Arduino's own UNO Rev3e board file (CC BY-SA 4.0): traces, pads and silkscreen are drawn on
# the top from it (board_art.py). The Uno prints its labels from layer 25 as well as 21.
BRD = HERE / "reference" / "boards" / "UNO-TH_Rev3e.brd"
OX, OY = 33.04, 27.26
PCB_T = 1.4   # the model's board thickness

TEAL = (0.00, 0.58, 0.60)      # Arduino's board colour (official photos)
STEEL = (0.74, 0.75, 0.78)
SILVER = (0.86, 0.86, 0.88)
BLACK = (0.08, 0.08, 0.09)
TRACE = (0.05, 0.66, 0.66)      # copper under the mask, a shade lighter
TIN = (0.80, 0.81, 0.83)        # the Uno's pads are tinned, not gold


CAPS = []   # (x, y, r) of the electrolytic caps in model coordinates, found in main()


def find_caps(shape):
    """Centres of the round 2.5 to 4.5 mm radius faces standing above 5 mm: the caps."""
    caps = []
    for f in shape.Faces():
        if f.geomType() == "CYLINDER" and f.BoundingBox().zmax > 5:
            c = f._geomAdaptor().Cylinder()
            if 2.5 <= c.Radius() <= 4.5:
                p = c.Location()
                if p.X() + OX < 16 and p.Y() + OY < 15:
                    continue                      # the power jack's barrel, not a cap
                if all(abs(p.X() - x) > 0.5 or abs(p.Y() - y) > 0.5 for x, y, _ in caps):
                    caps.append((p.X(), p.Y(), c.Radius()))
    return caps


def colour_of(face):
    b = face.BoundingBox()
    for cx, cy, r in CAPS:   # cans and their tops
        if b.zmax > 5 and max(abs(b.xmin - cx), abs(b.xmax - cx), abs(b.ymin - cy), abs(b.ymax - cy)) <= r + 0.2:
            return SILVER
    if b.zmax <= PCB_T + 0.01:
        return TEAL
    x, y = (b.xmin + b.xmax) / 2 + OX, (b.ymin + b.ymax) / 2 + OY
    if x < 17 and 28 < y < 48:
        return STEEL                                  # USB-B socket
    if x < 16 and y < 15:
        return BLACK                                  # power jack, barrel included
    if 12 < x < 26 and 22 < y < 31:
        return SILVER                                 # 16 MHz crystal (HC-49)
    if x < 11 and y > 45:
        return STEEL                                  # reset button
    if face.geomType() == "CYLINDER":
        r = face._geomAdaptor().Cylinder().Radius()
        if 2.5 <= r <= 4.5 and b.zmax > 5:
            return SILVER                             # electrolytic caps
    return BLACK


def uno_assembly(art=True):
    """The Uno as a cq.Assembly: the model with per-face colours, plus the artwork sheets."""
    src = FIXED if FIXED.exists() else SRC
    shape = cq.importers.importStep(str(src)).val()
    # The model's raised "UNO" oval logo (nothing else stands there) would poke through the
    # real silkscreen drawn by board_art, so shave it off.
    logo = cq.Solid.makeBox(14.0, 6.4, 0.5, cq.Vector(42.5 - OX, 34.8 - OY, PCB_T + 0.001))
    shape = shape.cut(logo).clean()
    CAPS[:] = find_caps(shape)
    a = cq.Assembly(name="arduino_uno_r3")
    a.add(shape, name="uno", color=cq.Color(*TEAL))
    for face in shape.Faces():
        c = colour_of(face)
        if c != TEAL:
            a.addSubshape(face, color=cq.Color(*c))
    try:
        import board_art as ba
    except ImportError:
        ba = None
    if art and ba is not None and BRD.exists():
        art_colours = dict(ba.COLOURS, copper=TRACE, pads=TIN)
        layers = ba.board_art(str(BRD), plain_silk=("21", "25"))
        for layer, sheet in ba.art_solids(layers, PCB_T, offset=(-OX, -OY)).items():
            a.add(sheet, name=f"art_{layer}", color=cq.Color(*art_colours[layer]))
    return a, src


def main():
    a, src = uno_assembly(art=False)
    a.export(str(OUT))
    print("wrote", OUT, "from", src.name)


if __name__ == "__main__":
    main()
