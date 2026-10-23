"""Colour mikeoverbay's Arduino Uno STEP model (one fused solid, no colours) by face, so it
looks like the real board next to the coloured Music Maker model.

STEP can carry colours per face (but no textures). Faces are sorted by where they are:
  - the PCB slab (z 0 to 1.4)      -> Arduino teal
  - the USB-B socket region         -> steel
  - the power jack region           -> black
  - round faces 2.5 to 4.5 mm radius (the electrolytic caps) -> silver
  - everything else on top          -> black (headers, power jack, chips, button)
Model coordinates = Uno coordinates - (33.04, 27.26); Uno x from the USB end, y from the
power-header edge.

Run:  python color_uno.py   ->  reference/arduino_uno_r3_coloured.step
"""
from pathlib import Path

import cadquery as cq
from OCP.IFSelect import IFSelect_RetDone
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_ColorSurf, XCAFDoc_DocumentTool

HERE = Path(__file__).resolve().parent
SRC = HERE / "reference" / "arduino_uno_r3.step"
FIXED = Path.home() / "OneDrive" / "Desktop" / "STEP files" / "ARDUINO UNO R3 Step - fixed to Arduino drawing.STEP"
OUT = HERE / "reference" / "arduino_uno_r3_coloured.step"
OX, OY = 33.04, 27.26
PCB_T = 1.4   # the model's board thickness

TEAL = (0.00, 0.53, 0.57)
STEEL = (0.74, 0.75, 0.78)
SILVER = (0.86, 0.86, 0.88)
BLACK = (0.08, 0.08, 0.09)


def colour_of(face):
    b = face.BoundingBox()
    if b.zmax <= PCB_T + 0.01:
        return TEAL
    x, y = (b.xmin + b.xmax) / 2 + OX, (b.ymin + b.ymax) / 2 + OY
    if x < 17 and 28 < y < 48:
        return STEEL                                  # USB-B socket
    if x < 16 and y < 15:
        return BLACK                                  # power jack, barrel included
    if face.geomType() == "CYLINDER":
        r = face._geomAdaptor().Cylinder().Radius()
        if 2.5 <= r <= 4.5 and b.zmax > 5:
            return SILVER                             # electrolytic caps
    return BLACK


def main():
    src = FIXED if FIXED.exists() else SRC
    shape = cq.importers.importStep(str(src)).val()
    doc = TDocStd_Document(TCollection_ExtendedString("uno"))
    shapes = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    colours = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    label = shapes.AddShape(shape.wrapped, False)
    for face in shape.Faces():
        sub = shapes.AddSubShape(label, face.wrapped)
        r, g, b = colour_of(face)
        colours.SetColor(sub, Quantity_Color(r, g, b, Quantity_TOC_RGB), XCAFDoc_ColorSurf)
    writer = STEPCAFControl_Writer()
    writer.SetColorMode(True)
    writer.Transfer(doc, STEPControl_AsIs)
    assert writer.Write(str(OUT)) == IFSelect_RetDone
    print("wrote", OUT, "from", src.name)


if __name__ == "__main__":
    main()
