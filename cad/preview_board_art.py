"""Top-view render of a board's artwork on a plain board, to compare with photos."""
import sys
import cadquery as cq, vtk
from cadquery.vis import toVTKAssy
import board_art as ba

def render(brd, outline, board_rgb, copper_rgb, out, plain_silk=("21",)):
    plate = cq.Workplane("XY").polyline(outline).close().extrude(1.6).val()
    a = cq.Assembly().add(plate, name="pcb", color=cq.Color(*board_rgb))
    cols = dict(ba.COLOURS, copper=copper_rgb)
    for n, s in ba.art_solids(ba.board_art(brd, plain_silk=plain_silk), 1.6).items():
        a.add(s, name=n, color=cq.Color(*cols[n]))
    r = vtk.vtkRenderer(); r.SetBackground(0.25, 0.25, 0.27)
    for it in toVTKAssy(a, edges=False): r.AddViewProp(it)
    w = vtk.vtkRenderWindow(); w.SetOffScreenRendering(1); w.AddRenderer(r); w.SetSize(1400, 1100)
    cam = r.GetActiveCamera(); cam.ParallelProjectionOn(); cam.SetFocalPoint(34.3, 26.7, 0); cam.SetPosition(34.3, 26.7, 200); cam.SetViewUp(0, 1, 0)
    r.ResetCamera(); cam.Zoom(1.25); w.Render()
    f = vtk.vtkWindowToImageFilter(); f.SetInput(w); f.Update()
    p = vtk.vtkPNGWriter(); p.SetFileName(out); p.SetInputConnection(f.GetOutputPort()); p.Write()

if __name__ == "__main__":
    import music_maker_shield as mm
    render("reference/boards/Adafruit-Music-Maker-MP3-Shield-RevE.brd", mm.OUTLINE, (0.06, 0.30, 0.78), (0.12, 0.40, 0.90), "previews/music_maker_art_top.png")
    uno = [(0, 0), (66.04, 0), (66.04, 1.27), (68.58, 3.81), (68.58, 37.85), (66.04, 40.39), (66.04, 51.82), (64.52, 53.34), (0, 53.34)]
    render("reference/boards/UNO-TH_Rev3e.brd", uno, (0.00, 0.55, 0.57), (0.05, 0.62, 0.62), "previews/uno_art_top.png", ("21", "25"))
    print("ok")
