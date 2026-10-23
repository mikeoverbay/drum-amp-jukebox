"""The drum player's full assembly for viewing: mikeoverbay's hood (drum_case_hood.step, his
Shapr3D edit), the bottom cover, the screen, and the coloured Uno and Music Maker models with
their board artwork, each placed where drum_case.py puts them.

Run:  python make_assembly.py   ->  drum_case_assembly.step
"""
from pathlib import Path

import cadquery as cq
from OCP.gp import gp_Trsf

import color_uno
import drum_case as dc
import music_maker_shield as mm

HERE = Path(__file__).resolve().parent
OUT = HERE / "drum_case_assembly.step"   # no board artwork: opens in Shapr3D (6.8 MB)
# With the board artwork as thin sheets (33 MB): Shapr3D crashes on it; there, put the
# decals/*.png images on the boards instead.
OUT_ART = HERE / "drum_case_assembly_with_artwork.step"
HOOD = HERE / "drum_case_hood.step"
COVER = HERE / "drum_case_bottom_cover.step"
BEIGE, DARK_BEIGE = cq.Color(0.87, 0.82, 0.70), cq.Color(0.70, 0.66, 0.56)


def uno_location():
    """Uno model coordinates -> case, as drum_case.uno_model() places the model."""
    ox, oy = dc.UNO_MODEL_XY
    t = gp_Trsf()
    t.SetValues(0, -1, 0, dc.UNO_X - (oy - dc.UNO_W / 2), -1, 0, 0, dc.uno_edge - ox, 0, 0, -1, dc.uno_back_z)
    return cq.Location(t)


def shield_location():
    """Music Maker board coordinates -> case, as drum_case.music_maker_model() does."""
    t = gp_Trsf()
    t.SetValues(0, -1, 0, dc.UNO_X + dc.UNO_W / 2, -1, 0, 0, dc.uno_edge, 0, 0, -1,
                dc.uno_back_z - dc.UNO_PCB_T - dc.MM_GAP)
    return cq.Location(t)


def build(art=True):
    a = cq.Assembly(name="drum_player")
    a.add(cq.importers.importStep(str(HOOD)).val(), name="hood", color=BEIGE)
    a.add(cq.importers.importStep(str(COVER)).val(), name="bottom_cover", color=DARK_BEIGE)
    disp = dc.display_model()
    if disp is not None:
        a.add(disp, name="display_DisplayV2", color=cq.Color(0.1, 0.4, 0.2))
    uno, _ = color_uno.uno_assembly(art)
    a.add(uno, name="arduino_uno", loc=uno_location())
    a.add(mm.shield_assembly(art), name="music_maker", loc=shield_location())
    return a


def main():
    for art, out in ((False, OUT), (True, OUT_ART)):
        build(art).export(str(out))
        print("wrote", out)


if __name__ == "__main__":
    main()
