"""Board artwork as decal images for Shapr3D (Visualization > decals): the top side of each
board drawn from its Eagle file (board_art.py), seen straight down, cropped exactly to the
board's outline (transparent outside it), DECAL_PX_PER_MM pixels per mm. Apply it to the
board's top face and size it to the board (Music Maker and Uno: 68.58 x 53.34 mm).

Run:  python make_decals.py  ->  decals/*.png
"""
from pathlib import Path

import cadquery as cq
import vtk
from cadquery.vis import toVTKAssy
from PIL import Image, ImageDraw

import board_art as ba

HERE = Path(__file__).resolve().parent
OUT = HERE / "decals"
DECAL_PX_PER_MM = 40
W, H = 68.58, 53.34
UNO_OUTLINE = [(0, 0), (66.04, 0), (66.04, 1.27), (68.58, 3.81), (68.58, 37.85), (66.04, 40.39),
               (66.04, 51.82), (64.52, 53.34), (0, 53.34)]


def decal(brd, outline, board_rgb, copper_rgb, pads_rgb, out, plain_silk=("21",)):
    plate = cq.Workplane("XY").polyline(outline).close().extrude(1.6).val()
    a = cq.Assembly().add(plate, name="pcb", color=cq.Color(*board_rgb))
    cols = dict(ba.COLOURS, copper=copper_rgb, pads=pads_rgb)
    for n, s in ba.art_solids(ba.board_art(brd, plain_silk=plain_silk), 1.6).items():
        a.add(s, name=n, color=cq.Color(*cols[n]))
    px, py = round(W * DECAL_PX_PER_MM), round(H * DECAL_PX_PER_MM)
    r = vtk.vtkRenderer()
    r.SetBackground(0, 0, 0)
    for it in toVTKAssy(a, edges=False):
        it.GetProperty().SetAmbient(1.0) if hasattr(it, "GetProperty") else None
        it.GetProperty().SetDiffuse(0.0) if hasattr(it, "GetProperty") else None
        r.AddViewProp(it)
    w = vtk.vtkRenderWindow()
    w.SetOffScreenRendering(1)
    w.AddRenderer(r)
    w.SetSize(px, py)
    cam = r.GetActiveCamera()
    cam.ParallelProjectionOn()
    cam.SetFocalPoint(W / 2, H / 2, 0)
    cam.SetPosition(W / 2, H / 2, 100)
    cam.SetViewUp(0, 1, 0)
    cam.SetParallelScale(H / 2)
    r.ResetCameraClippingRange()
    w.Render()
    f = vtk.vtkWindowToImageFilter()
    f.SetInput(w)
    f.Update()
    tmp = str(out) + ".tmp.png"
    p = vtk.vtkPNGWriter()
    p.SetFileName(tmp)
    p.SetInputConnection(f.GetOutputPort())
    p.Write()
    img = Image.open(tmp).convert("RGBA")
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon([(x * DECAL_PX_PER_MM, (H - y) * DECAL_PX_PER_MM) for x, y in outline], fill=255)
    img.putalpha(mask)
    img.save(out)
    Path(tmp).unlink()
    print("wrote", out, img.size)


if __name__ == "__main__":
    import music_maker_shield as mm
    import color_uno as cu
    OUT.mkdir(exist_ok=True)
    decal(str(mm.BRD), mm.OUTLINE, mm.SOLDERMASK.toTuple()[:3], mm.TRACE.toTuple()[:3], ba.COLOURS["pads"],
          OUT / "music_maker_rev_e_top_decal.png")
    decal(str(cu.BRD), UNO_OUTLINE, cu.TEAL, cu.TRACE, cu.TIN, OUT / "arduino_uno_r3_top_decal.png", ("21", "25"))
