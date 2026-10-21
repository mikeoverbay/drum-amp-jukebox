"""Console-style case for the drum-amp MP3 player, now on an Arduino Uno + shield stack.

Same look as the console case (vertical front lip, 30 degree screen face with the Ender-3 V2
DWIN screen and knob built in, flat plain deck), but only as deep as the stack needs. The
Uno hangs upside down under the deck on four D-shaped standoffs, exactly like the console;
its USB, barrel jack and the shield's audio jack face the back, through an opening in the
tray's back wall.

Two printed parts:
  hood - sides, front lip, screen face and deck in one piece, with the Uno standoffs.
  tray - bottom + back wall in one piece, screwed up into the hood from below.

Coordinates (mm): X = width (knob side +X), Y = depth (front at 0), Z = up.
Exported in assembled position.

Run:  python drum_case.py
"""
import math
from pathlib import Path

import cadquery as cq
from OCP.BRep import BRep_Tool
from OCP.ShapeFix import ShapeFix_Wire
from OCP.TopExp import TopExp

HERE = Path(__file__).resolve().parent
SHIELD_DIR = HERE / "vs1053_shield"     # HW-261 VS1053 shield model (from the 4560 cap session)
UNO_STEP = HERE / "reference" / "arduino_uno_r3.step"   # mikeoverbay's Uno model
UNO_MODEL_XY = (33.04, 27.26)           # model x, y + this = Uno coordinates (matched on its 4 holes)
DISPLAY_STEP = HERE / "reference" / "DisplayV2.step"

# ---------------------------------------------------------------------------
# Display (same as console case\console_case.py, caliper-checked)
# ---------------------------------------------------------------------------
BOARD_W, BOARD_H, BOARD_T = 141.0, 74.0, 1.7
_hx, _hy = (60.95, 57.46), (36.95, 33.10)
KNOB_X = 138.41 - 6.0
BOARD_HOLES = [(_hx[0] - _hx[1], _hy[0] - _hy[1]), (_hx[0] - _hx[1], _hy[0] + _hy[1]),
               (_hx[0] + _hx[1], _hy[0] - _hy[1]), (_hx[0] + _hx[1], _hy[0] + _hy[1]), (KNOB_X, 26.0)]
LCD = (8.0, 114.0, 3.0, 71.0)
LCD_H = 5.2
VA = (12.2, 109.9, 11.2, 67.7)
ENC = (KNOB_X, 39.0)
ENC_BODY, ENC_BODY_H = 12.0, 6.6
ENC_SHAFT_D, ENC_SHAFT_TOP = 6.7, 21.21
BACK_PARTS = [
    (15.2, 24.4, 20.0, 40.7, 9.6),       # 2x5 ribbon header
    (120.6, 129.8, 52.0, 61.2, 5.6),     # buzzer
    (30.0, 37.0, 51.1, 58.1, 5.4),       # capacitor
    (50.6, 57.6, 51.1, 58.1, 5.4),       # capacitor
    (26.3, 49.9, 39.7, 45.5, 1.8),       # LCD flex connector
    (30.0, 45.0, 7.0, 22.2, 1.8),        # SD socket
    (KNOB_X - 6.0, KNOB_X + 6.0, 33.0, 45.0, 4.0),   # encoder pins (estimate)
]
HEADER = BACK_PARTS[0]
RIBBON_PLUG = 8.0

# ---------------------------------------------------------------------------
# Electronics: Arduino Uno R3 + one shield, hanging under the deck (as console_case.py)
# ---------------------------------------------------------------------------
UNO_L, UNO_W = 68.58, 53.34
UNO_HOLES = [(15.24, 3.71), (15.24, 50.80), (66.04, 7.62), (66.04, 35.56)]  # x from the USB edge; first hole from the Uno STEP model (as console_case.py)
UNO_USB_OVERHANG = 6.86   # USB-B past the board edge (Uno STEP model)
STANDOFF_DROP = 25.0   # standoffs this much longer, so the board hangs lower in the case (mikeoverbay)
STANDOFF_H, STANDOFF_D, UNO_PILOT_D = 5.0 + STANDOFF_DROP, 9.0, 2.5
STANDOFF_FLAT = 2.5    # D-shaped standoffs: flat this far from the hole, on the side facing the Uno's centre
HANG_PILOT = 5.8       # pilot depth for 3 x 6 mm screws through the 1.6 mm Uno (as the console)
MIN_SKIN = 1.0         # plastic required between a pilot and the outside of the hood
# Stack: Uno + HW-261 VS1053 shield (vs1053_shield/vs1053_shield.py, +-1 mm from photos).
UNO_FAR_PARTS = 66.0   # Uno parts (ICSP header) stop this far from the USB edge; the board is 68.58
SHIELD_GAP, SHIELD_PCB_T, SHIELD_SOCKET_H = 11.0, 1.6, 8.5   # Uno PCB top to shield PCB; shield's tallest parts
STACK_H = STANDOFF_H + 1.6 + SHIELD_GAP + SHIELD_PCB_T + SHIELD_SOCKET_H   # 27.7, standoffs included
UNO_SOLDER = 2.0       # pins and solder on the Uno's back, which faces the deck when hanging
STACK_CLEAR = 3.0      # minimum gap between the stack and the display's parts
SLOPE_CLEAR = 1.0      # Uno's back to the inside of the slope
# T-shaped case: full width at the front for the screen; behind it both sides step in to the
# Uno's length, so the Uno (on the centre line, USB end to +X) shows its plugs on both sides:
# the USB-B flush in the right step, the shield's headphone and mic jacks proud of the left.
# Openings are snug; the narrow side walls flex to pop the board in.
USB_B = (12.82, 12.5, 35.60)  # Uno USB-B body: width (along Y), height below the board, centre y (Uno STEP model)
BARREL = (9.0, 6.5, 7.6, 10.0)   # Uno power jack: hole size, centre below the board, centre y, plug hole dia (+-1 mm)
BARREL_HOLE = False         # power comes in by wire (mikeoverbay); True adds the power-jack hole
OPEN_CLEAR = 0.3            # clearance round every connector and board edge in the walls
USB_CLEAR = 1.5             # extra-roomy clearance round the USB-B body (mikeoverbay)
USB_BOARD_T = 1.4           # the Uno model's board thickness, which the USB-B height is measured from
SHIELD_JACK_FRONT_X = 70.93  # shield jack fronts, from the Uno's USB edge (vs1053_shield.JACK_FRONT_X)
JACK_OUT = 0.5              # jacks stand this far proud of the recess round them
LEFT_WIDEN = 1.5            # left step moved out so the board ends clear its inside face (mikeoverbay);
                            # an outside recess this deep round the jacks keeps them JACK_OUT proud
JACK_RECESS_MARGIN = 2.5    # recess reaches this far beyond the jack holes
JACK_CLEAR = 1.5            # clearance round the jacks (mikeoverbay)
JACK_HOLE_D = 5.8 + 2 * JACK_CLEAR   # 5.8 mm jack barrels
STEP_CLEAR = 9.5            # step walls' inner face to the screen's parts: room to take the screen out
REAR_CLEAR = 12.0           # shield's back edge to the back wall: room for the two back pillars
UNO_BACK_SHIFT = 9.0        # Uno moved this far back from the tightest fit (mikeoverbay)

# All tray screws: 3 mm wood screws, 14 mm long (mikeoverbay).
SCREW_L, SCREW_PILOT_D = 14.0, 2.5

# ---------------------------------------------------------------------------
# Case (same proportions as the console)
# ---------------------------------------------------------------------------
TILT = 30.0
WALL = 3.0
BOTTOM_T = 3.0
BACK_T = 3.0
FRONT_FLOOR = 15.0
FRONT_H_MIN = 15.0
SCREEN_MARGIN = 14.05
LCD_GAP = 0.2
WINDOW_INSET = -0.4
WINDOW_CHAMFER = 1.2
KNOB_HOLE_D = ENC_SHAFT_D + 2.8
ENC_POCKET = ENC_BODY + 5.0              # 17 mm square: 2.5 mm round the encoder body (was +3.0, opened 1 mm all round)
ENC_POCKET_EXTRA = 0.5                   # pocket 2.1 mm deep into the 3 mm face (was 1.6); 0.9 mm of face left
BOSS_D = 7.0
BOARD_PILOT_D = 2.1
FLOOR_CLEAR = 2.0
R_SIDE, R_RIDGE, R_LIP = 4.0, 6.0, 3.0
R_BOTTOM = 2.0                           # bottom outside edges: the 3 mm walls leave room for 2 mm
CSK_D, SCREW_CLEAR_D, PILOT_D = 6.3, 3.4, 2.5
BLOCK = 10.0                             # tray screw block width
BLOCK_H = SCREW_L - 3.0 + 2.0            # height: the 14 mm screw goes 11 mm in, plus 2 mm of plastic
VENT_SIDES = ()                          # no vent grooves: the narrow sides carry the plugs
VENT_N, VENT_PITCH, VENT_W, VENT_DEPTH, VENT_TOP = 6, 3.5, 1.6, 1.0, 9.0
DECK_SEAM = False                        # Apple II lid-seam groove on the deck (off: plain deck)
SEAM_INSET, SEAM_W, SEAM_DEPTH = 9.0, 1.2, 0.8
DECK_TEXT = ""
DECK_TEXT_FONT = r"C:\Windows\Fonts\arialbd.ttf"
DECK_TEXT_MAX = (120.0, 16.0)
DECK_TEXT_DEPTH = 1.0
DECK_TEXT_CHAMFER = 1.0                  # bottom band of the letters narrowing at 45 deg, so they print face down
                                         # without support; = DECK_TEXT_DEPTH makes the ~2 mm strokes V-shaped
FOOT_D, FOOT_DEPTH = 10.0, 1.0
HOOD_BACK_LIP = 3.0                      # hood sides and deck run this far past the tray's back wall (back sits recessed)
# Back screw pillars behind the Uno: from the deck down to the tray floor, screwed from below.
PILLAR_D = 10.0
PILLAR_XS = (-20.0, 20.0)               # two back pillars behind the Uno
RIB_T, RIB_L = 3.0, 8.0                  # gussets at the top of the pillar: thickness, reach along the deck (45 deg)

# ---------------------------------------------------------------------------
# Derived geometry
# ---------------------------------------------------------------------------
T = math.radians(TILT)
sinT, cosT, tanT = math.sin(T), math.cos(T), math.tan(T)
X = cq.Vector(1, 0, 0)
U = cq.Vector(0, cosT, sinT)
N = cq.Vector(0, -sinT, cosT)

W = BOARD_W + 2 * SCREEN_MARGIN
L_slope = BOARD_H + 2 * SCREEN_MARGIN
s_c = L_slope / 2
pcb_depth = WALL + LCD_GAP + LCD_H


def board_sd(by):
    return s_c + by - BOARD_H / 2


hx0, hx1, hy0, hy1, hdep = HEADER
FRONT_H = max([FRONT_H_MIN] + [BOTTOM_T + FLOOR_CLEAR - (board_sd(y0) * sinT - d * cosT) for y0, d in (
    (0, pcb_depth + BOARD_T), (hy0 - 1, pcb_depth + BOARD_T + hdep + RIBBON_PLUG))])
H = FRONT_H + L_slope * sinT
y_ridge = L_slope * cosT

face_plane = cq.Plane(origin=(cq.Vector(0, 0, FRONT_H) + U * s_c).toTuple(), xDir=(1, 0, 0), normal=N.toTuple())
board_plane = cq.Plane(origin=(cq.Vector(0, 0, FRONT_H) + U * (s_c - BOARD_H / 2)
                               - X * (BOARD_W / 2) - N * pcb_depth).toTuple(),
                       xDir=(1, 0, 0), normal=N.toTuple())
BOARD_LOC = cq.Location(board_plane)

def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def board_box(x0, x1, y0, y1, z0, z1):
    return box(x0, x1, y0, y1, z0, z1).moved(BOARD_LOC)


def display_keepout():
    parts = [board_box(0, BOARD_W, 0, BOARD_H, -BOARD_T, 0),
             board_box(LCD[0], LCD[1], LCD[2], LCD[3], 0, LCD_H),
             board_box(ENC[0] - ENC_BODY / 2, ENC[0] + ENC_BODY / 2, ENC[1] - ENC_BODY / 2,
                       ENC[1] + ENC_BODY / 2, 0, ENC_BODY_H)]
    for x0, x1, y0, y1, dep in BACK_PARTS:
        parts.append(board_box(x0, x1, y0, y1, -BOARD_T - dep, -BOARD_T))
    parts.append(board_box(hx0 - 1, hx1 + 1, hy0 - 1, hy1 + 1, -BOARD_T - hdep - RIBBON_PLUG, -BOARD_T - hdep))
    return parts


stack_z0, stack_z1 = H - WALL - STACK_H, H - WALL      # stack, standoffs included
uno_back_z = H - WALL - STANDOFF_H                     # Uno's back (faces up when hanging)


def stack_y_front_min():
    """Smallest Y for the stack's front face that keeps STACK_CLEAR from every display part
    and keeps the Uno's solder side SLOPE_CLEAR from the inside of the slope."""
    keep = cq.Compound.makeCompound(display_keepout())
    lo, hi = 0.0, 250.0
    for _ in range(30):
        mid = (lo + hi) / 2
        stack = box(uno_usb_x - UNO_L, uno_usb_x + UNO_USB_OVERHANG, mid, mid + UNO_W, stack_z0, stack_z1)
        lo, hi = (lo, mid) if stack.distance(keep) >= STACK_CLEAR else (mid, hi)
    return max(hi, (uno_back_z + UNO_SOLDER + SLOPE_CLEAR - FRONT_H + WALL / cosT) / tanT)


uno_usb_x = (SHIELD_JACK_FRONT_X - UNO_USB_OVERHANG) / 2  # Uno centred: USB face and jack fronts equally far out
XR = uno_usb_x + UNO_USB_OVERHANG                      # right step's outer face (USB face flush)
XL = uno_usb_x - SHIELD_JACK_FRONT_X + JACK_OUT - LEFT_WIDEN   # left step's outer face
stack_front = stack_y_front_min()
uno_y0 = stack_front + UNO_BACK_SHIFT                  # Y of the Uno's power-header edge (front)
SHIELD_BACK = 55.6                                      # shield's back edge, from the Uno's power edge (overhangs ~1.2 mm)
D = uno_y0 + SHIELD_BACK + REAR_CLEAR + BACK_T


def uno_xy(ux, uy):
    """Uno coordinates (x from the USB edge, y from the power-header edge) -> case X, Y.
    Hanging upside down, turned so the USB faces +X: power header to the front."""
    return uno_usb_x - ux, uno_y0 + uy


def uno_standoffs():
    """D-shaped standoffs at the Uno's holes (flat facing its centre) and their pilots."""
    cx, cy = uno_xy(UNO_L / 2, UNO_W / 2)
    bosses, pilots = [], []
    for ux, uy in UNO_HOLES:
        x, y = uno_xy(ux, uy)
        zb, zt = uno_back_z, H - WALL + 0.5
        boss = cq.Solid.makeCylinder(STANDOFF_D / 2, zt - zb, cq.Vector(x, y, zb))
        flat = (cq.Solid.makeBox(STANDOFF_D, 2 * STANDOFF_D, zt - zb + 2, cq.Vector(STANDOFF_FLAT, -STANDOFF_D, zb - 1))
                .rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), math.degrees(math.atan2(cy - y, cx - x)))
                .translate(cq.Vector(x, y, 0)))
        bosses.append(boss.cut(flat))
        # Gussets: four 45 degree ribs from the top of each long standoff to the deck.
        r = STANDOFF_D / 2
        prof = [(0, zt), (r + RIB_L, zt), (r + RIB_L, H - WALL), (0, H - WALL - RIB_L - r)]
        for ang in (0, 90, 180, 270):
            rib = (cq.Workplane("XZ").polyline(prof).close().extrude(RIB_T / 2, both=True).val()
                   .rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), ang).translate(cq.Vector(x, y, 0)))
            bosses.append(rib)
        pilots.append(cq.Solid.makeCylinder(UNO_PILOT_D / 2, HANG_PILOT + 0.01, cq.Vector(x, y, zb - 0.01)))
    return bosses, pilots


def stack_envelope():
    """Uno + shield placeholders, from the Uno's back down (the standoffs belong to the hood):
    the board stack, and the USB-B body sticking out through the right wall."""
    x0, y0 = uno_xy(UNO_L, 0)
    x1, y1 = uno_xy(0, UNO_W)
    uw, uh, uyc = USB_B
    _, uy = uno_xy(0, uyc)
    utop = uno_back_z - 1.6
    shield_bot = utop - SHIELD_GAP                        # shield PCB face toward the Uno
    xe, _ = uno_xy(UNO_FAR_PARTS, 0)                     # parts between the boards stop short of the far end
    parts = [box(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), utop, uno_back_z)
             .fuse(box(xe, max(x0, x1), min(y0, y1), max(y0, y1), shield_bot, utop)),
             box(uno_usb_x, uno_usb_x + UNO_USB_OVERHANG, uy - uw / 2, uy + uw / 2,
                 uno_back_z - USB_BOARD_T - uh, uno_back_z - USB_BOARD_T)]
    return parts + [s for s, _ in shield_parts_in_case().values()]


def _shield_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("vs1053_shield", SHIELD_DIR / "vs1053_shield.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def shield_parts_in_case():
    """The HW-261 shield's parts, hanging under the Uno: Uno coordinates turned 180 degrees about Y
    (x -> -X from the USB edge, y -> +Y from the power edge, components facing down)."""
    loc = cq.Location(cq.Vector(uno_usb_x, uno_y0, uno_back_z - 1.6 - SHIELD_GAP), cq.Vector(0, 1, 0), 180)
    return {k: (v.moved(loc), c) for k, (v, c) in _shield_module().shield_parts().items()}


def jack_case_xyz(name="headphone out"):
    """Case X of the jack's front face, and the jack centre's Y and Z."""
    m = _shield_module()
    zc = uno_back_z - 1.6 - SHIELD_GAP - (m.PCB_T + m.JACK_H / 2)
    return uno_usb_x - m.JACK_FRONT_X, uno_y0 + m.JACKS[name], zc


def rounded_rect(w, h, r):
    return cq.Sketch().rect(w, h).vertices().fillet(r) if r > 0 else cq.Sketch().rect(w, h)


def plane_prism(plane, cx, cy, w, h, depth, r=0.0, start=0.0):
    wp = cq.Workplane(plane).workplane(offset=-start).center(cx, cy)
    return wp.placeSketch(rounded_rect(w, h, r)).extrude(-depth).val()


def plane_cyl(plane, cx, cy, dia, depth, start=0.0):
    p = plane.toWorldCoords((cx, cy, -start))
    return cq.Solid.makeCylinder(dia / 2, depth, p, -plane.zDir)


def face_xy(bx, by):
    return bx - BOARD_W / 2, by - BOARD_H / 2


# ---------------------------------------------------------------------------
# Hood
# ---------------------------------------------------------------------------
def outer_solid():
    prof = [(0, 0), (0, FRONT_H), (y_ridge, H), (D + HOOD_BACK_LIP, H), (D + HOOD_BACK_LIP, 0)]
    s = cq.Workplane("YZ").polyline(prof).close().extrude(W / 2, both=True).val()
    for pt, r in (((0, y_ridge, H), R_RIDGE), ((0, 0, FRONT_H), R_LIP)):
        e = min(s.Edges(), key=lambda e: (e.Center() - cq.Vector(*pt)).Length)
        s = s.fillet(r, [e])
    side_edges = []
    for f in s.Faces():
        if abs(f.normalAt().x) > 0.99:
            for e in f.Edges():
                bb = e.BoundingBox()
                if bb.zmax < 0.01 or bb.ymin > D + HOOD_BACK_LIP - 0.01:
                    continue
                side_edges.append(e)
    try:
        s = s.fillet(R_SIDE, side_edges)
    except Exception as ex:
        print("side fillet skipped:", ex)
    return s


def step_y():
    """Y of the steps' outer (back) face: the step walls stay STEP_CLEAR behind the screen's parts."""
    keep = cq.Compound.makeCompound(display_keepout())
    return keep.BoundingBox().ymax + STEP_CLEAR + WALL


def t_outer():
    """Full width up to the steps, then only XL..XR to the back."""
    full = outer_solid()
    ys = step_y()
    wings = full.intersect(box(-W, W, -1, ys, -1, H + 1))
    narrow = full.intersect(box(XL, XR, ys - 1, D + HOOD_BACK_LIP + 1, -1, H + 1))
    solid = round_sharp_edges(wings.fuse(narrow).clean(), R_SIDE)
    bottom = [e for e in solid.Edges() if e.BoundingBox().zmax < 0.01]
    try:
        return solid.fillet(R_BOTTOM, bottom)
    except Exception as ex:
        print("bottom edges left sharp:", ex)
        return solid


def round_sharp_edges(solid, r):
    """Fillet every sharp edge that isn't on the bottom: corners, the steps and the deck edges.
    Edges where two faces already meet smoothly (the ridge and lip roundings) are skipped.
    Vertical edges first, then the rest (OCC blends the corners better that way); any edge
    that won't take r is retried alone at smaller radii."""
    def sharp_edges(sol, vertical):
        out = []
        for e in sol.Edges():
            bb = e.BoundingBox()
            if bb.zmax < 0.01:
                continue
            if vertical != (bb.zlen > 5 * max(bb.xlen, bb.ylen, 1e-6)):
                continue
            faces = e.ancestors(sol, "Face").Faces()
            if len(faces) != 2:
                continue
            c = e.Center()
            if faces[0].normalAt(c).dot(faces[1].normalAt(c)) < 0.999:
                out.append(e)
        return out
    sharp_left = 0
    for vertical in (True, False):
        edges = sharp_edges(solid, vertical)
        try:
            solid = solid.fillet(r, edges)
            continue
        except Exception:
            pass
        for rr in (r, r * 0.75, r * 0.5):
            left = []
            for e in edges:
                try:
                    solid = solid.fillet(rr, [min(solid.Edges(), key=lambda x: (x.Center() - e.Center()).Length)])
                except Exception:
                    left.append(e)
            edges = left
            if not edges:
                break
        sharp_left += len(edges)
    if sharp_left:
        print(f"{sharp_left} edge(s) left sharp")
    return solid


def t_cavity():
    full = cavity()
    ys = step_y()
    return full.intersect(box(-W, W, -2, ys - WALL, -2, H)).fuse(
        full.intersect(box(XL + WALL, XR - WALL, -2, D + HOOD_BACK_LIP + 2, -2, H))).clean()


def cavity():
    z_in = lambda y: FRONT_H + y * tanT - WALL / cosT
    y_ri = (H - WALL - FRONT_H + WALL / cosT) / tanT
    prof = [(WALL, BOTTOM_T), (WALL, z_in(WALL)), (y_ri, H - WALL), (D + HOOD_BACK_LIP + 1, H - WALL),
            (D + HOOD_BACK_LIP + 1, -1), (FRONT_FLOOR, -1), (FRONT_FLOOR, BOTTOM_T)]
    return cq.Workplane("YZ").polyline(prof).close().extrude(W / 2 - WALL, both=True).val()


def screen_features(hood):
    P = face_plane
    wx, wy = face_xy((VA[0] + VA[1]) / 2, (VA[2] + VA[3]) / 2)
    ww, wh = VA[1] - VA[0] - 2 * WINDOW_INSET, VA[3] - VA[2] - 2 * WINDOW_INSET
    hood = hood.cut(plane_prism(P, wx, wy, ww, wh, WALL + 2, 0.5, start=-1))
    c = WINDOW_CHAMFER
    hood = hood.cut(cq.Workplane(P).workplane(offset=0.01).center(wx, wy).rect(ww + 2 * c + 0.02, wh + 2 * c + 0.02)
                    .workplane(offset=-(c + 0.01)).rect(ww, wh).loft().val())
    kx, ky = face_xy(*ENC)
    hood = hood.cut(plane_cyl(P, kx, ky, KNOB_HOLE_D, WALL + 2, start=-1))
    pocket = ENC_BODY_H - (LCD_GAP + LCD_H) + 0.4 + ENC_POCKET_EXTRA
    hood = hood.cut(plane_prism(P, kx, ky, ENC_POCKET, ENC_POCKET, pocket + 0.01, 0.5, start=WALL - pocket))
    boss_len = LCD_GAP + LCD_H
    for hx, hy in BOARD_HOLES:
        bx, by = face_xy(hx, hy)
        hood = hood.fuse(plane_cyl(P, bx, by, BOSS_D, boss_len + 0.01, start=WALL - 0.01))
        hood = hood.cut(plane_cyl(P, bx, by, BOARD_PILOT_D, boss_len + WALL - 1.5, start=1.5))
    return hood


def deck_text_size():
    """Font size that fits DECK_TEXT inside DECK_TEXT_MAX and the lid seam."""
    probe = cq.Workplane("XY").text(DECK_TEXT, 10.0, 1.0, fontPath=DECK_TEXT_FONT).val().BoundingBox()
    seam_d = D - y_ridge - 2 * (SEAM_INSET + SEAM_W) - 4
    return 10.0 * min(DECK_TEXT_MAX[0] / probe.xlen, min(DECK_TEXT_MAX[1], seam_d) / probe.ylen)


def _inset_wires(wire, d):
    """2D offset of a wire (negative = inward). offset2D builds offset curves, which don't
    survive a STEP round trip, so those edges are re-fitted as B-splines."""
    def vpt(v):
        p = BRep_Tool.Pnt_s(v)
        return cq.Vector(p.X(), p.Y(), p.Z())

    out = []
    for w in wire.offset2D(d, "arc"):
        edges = []
        for e in w.Edges():
            if e.geomType() == "OFFSET":
                # End exactly on the original vertices so the neighbours still join up.
                p0, p1 = vpt(TopExp.FirstVertex_s(e.wrapped)), vpt(TopExp.LastVertex_s(e.wrapped))
                if (p1 - p0).Length < 1e-6:
                    continue
                if e.Length() < 0.01:
                    e = cq.Edge.makeLine(p0, p1)
                else:
                    e = cq.Edge.makeSpline([p0] + [e.positionAt(i / 23) for i in range(1, 23)] + [p1])
            edges.append(e)
        nw = cq.Wire.assembleEdges(edges)
        if not nw.IsClosed():
            fix = ShapeFix_Wire(nw.wrapped, cq.Face.makeFromWires(w).wrapped, 1e-4)
            fix.FixConnected()
            fix.FixClosed()
            nw = cq.Wire(fix.Wire())
        out.append(nw)
    return out


def deck_text():
    """DECK_TEXT as a solid for cutting into the deck, reading from the front. The bottom
    DECK_TEXT_CHAMFER of each letter narrows at 45 degrees, built as 0.1 mm steps of inset
    outlines (OCC's tapered extrude crashes on the font outlines)."""
    y = (y_ridge + D) / 2                        # centre of the lid seam
    letters = cq.Workplane("XY", origin=(0, y, 0)).text(
        DECK_TEXT, deck_text_size(), 1.0, fontPath=DECK_TEXT_FONT, halign="center", valign="center").val()
    z_band = H - DECK_TEXT_DEPTH + DECK_TEXT_CHAMFER      # top of the 45 degree band
    n = max(1, round(DECK_TEXT_CHAMFER / 0.1))
    step = DECK_TEXT_CHAMFER / n
    cutters = []
    for s in letters.Solids():
        face = min(s.Faces(), key=lambda f: f.Center().z)
        layers = [cq.Solid.extrudeLinear(face, cq.Vector(0, 0, H + 1 - z_band)).moved(cq.Location(cq.Vector(0, 0, z_band)))]
        for k in range(n):
            inset = (k + 0.5) * step
            z0 = z_band - (k + 1) * step
            try:
                outs = _inset_wires(face.outerWire(), -inset)
                holes = [w for iw in face.innerWires() for w in _inset_wires(iw, inset)]
            except Exception:  # the stroke has closed up at this depth
                continue
            if not outs:
                continue
            ext = lambda w: cq.Solid.extrudeLinear(cq.Face.makeFromWires(w), cq.Vector(0, 0, step + 0.01)).moved(
                cq.Location(cq.Vector(0, 0, z0)))
            layer = ext(outs[0]).fuse(*[ext(w) for w in outs[1:]]) if len(outs) > 1 else ext(outs[0])
            if holes:
                layer = layer.cut(*[ext(w) for w in holes])
            if layer.Volume() > 1e-6:
                layers.append(layer)
        cutters.append(layers[0].fuse(*layers[1:]).clean() if len(layers) > 1 else layers[0])
    return cq.Compound.makeCompound(cutters)


def block_xs():
    return [sx * (W / 2 - WALL - BLOCK / 2) for sx in (-1, 1)]


def pillar_xys():
    """Back screw pillars: behind the Uno, against the back wall."""
    return [(x, D - BACK_T - 0.3 - PILLAR_D / 2) for x in PILLAR_XS]


def wing_block_y():
    """Rear tray-screw blocks: in the wings, against the step walls."""
    return step_y() - WALL - 6


def make_hood():
    outer = t_outer()
    hood = screen_features(outer.cut(t_cavity()))
    # Front tray-screw blocks against the front lip (45 degree backs), as on the console.
    for bx in block_xs():
        prof = [(WALL - 0.5, BOTTOM_T), (FRONT_FLOOR + 16, BOTTOM_T), (FRONT_FLOOR + 6, BOTTOM_T + BLOCK_H),
                (WALL - 0.5, BOTTOM_T + BLOCK_H)]
        blk = cq.Workplane("YZ", origin=(bx, 0, 0)).polyline(prof).close().extrude(BLOCK / 2, both=True).val()
        hood = hood.fuse(blk.intersect(outer))
        hood = hood.cut(cq.Solid.makeCylinder(SCREW_PILOT_D / 2, BLOCK_H - 1.0, cq.Vector(bx, FRONT_FLOOR + 6, BOTTOM_T - 0.01)))
    # Rear tray-screw blocks at floor level in the wings' back corners, against the step walls.
    wy = wing_block_y()
    for bx in block_xs():
        hood = hood.fuse(box(bx - BLOCK / 2, bx + BLOCK / 2 + 0.5 * (1 if bx > 0 else -1), wy - 6, step_y() - WALL + 0.5,
                             BOTTOM_T, BOTTOM_T + BLOCK_H).intersect(outer))
        hood = hood.cut(cq.Solid.makeCylinder(SCREW_PILOT_D / 2, BLOCK_H - 1.0, cq.Vector(bx, wy, BOTTOM_T - 0.01)))
    # Back screw pillars from the deck to the tray floor, with 45 degree gussets to the deck
    # along the back wall (toward the Uno would hit it).
    top = H - WALL + 0.5
    r = PILLAR_D / 2
    for px, py in pillar_xys():
        hood = hood.fuse(cq.Solid.makeCylinder(r, top - BOTTOM_T - 0.3, cq.Vector(px, py, BOTTOM_T + 0.3)))
        prof = [(0, top), (r + RIB_L, top), (r + RIB_L, H - WALL), (0, H - WALL - RIB_L - r)]
        for sx in (-1, 1):   # in the XZ plane: local x = world X, local y = world Z
            rib = cq.Workplane("XZ", origin=(0, py, 0)).polyline([(px + sx * a, z) for a, z in prof]).close() \
                .extrude(RIB_T / 2, both=True).val()
            hood = hood.fuse(rib.intersect(outer))
        hood = hood.cut(cq.Solid.makeCylinder(SCREW_PILOT_D / 2, SCREW_L - BOTTOM_T + 1.0, cq.Vector(px, py, BOTTOM_T)))
    # Uno standoffs hanging from the deck, clipped to the outer shell.
    bosses, pilots = uno_standoffs()
    for b in bosses:
        hood = hood.fuse(b.intersect(outer))
    for pl in pilots:
        hood = hood.cut(pl)
    c = OPEN_CLEAR
    utop = uno_back_z - 1.6                       # Uno component side (faces down)
    # Right step: USB-B opening (body flush with the outside) and the power-jack hole.
    uw, uh, uyc = USB_B
    _, uy = uno_xy(0, uyc)
    uc, ut = USB_CLEAR, uno_back_z - USB_BOARD_T
    hood = hood.cut(box(XR - WALL - 1, XR + 1, uy - uw / 2 - uc, uy + uw / 2 + uc, ut - uh - uc, ut + uc))
    _, bz, byc, bd = BARREL
    _, by = uno_xy(0, byc)
    if BARREL_HOLE:
        hood = hood.cut(cq.Solid.makeCylinder(bd / 2, WALL + 2, cq.Vector(XR - WALL - 1, by, utop - bz), cq.Vector(1, 0, 0)))
    # Left step: jack barrels through, plus shallow pockets in its inside face for the Uno's
    # board edge, the shield's board edge and the jack bodies, which reach a little into it.
    m = _shield_module()
    xin = XL + WALL
    shield_bot = utop - SHIELD_GAP
    jys = [jack_case_xyz(n)[1] for n in m.JACKS]
    _, _, jz0 = jack_case_xyz()
    if LEFT_WIDEN > 0:   # outside recess round both jacks, rounded ends
        rr = JACK_HOLE_D / 2 + JACK_RECESS_MARGIN
        rec = (cq.Workplane("YZ", origin=(XL - 1, 0, 0)).center((min(jys) + max(jys)) / 2, jz0)
               .slot2D(max(jys) - min(jys) + 2 * rr, 2 * rr).extrude(1 + LEFT_WIDEN).val())
        hood = hood.cut(rec)
    for name in m.JACKS:
        _, jy, jz = jack_case_xyz(name)
        hood = hood.cut(cq.Solid.makeCylinder(JACK_HOLE_D / 2, WALL + 2, cq.Vector(XL - 1, jy, jz), cq.Vector(1, 0, 0)))
        jc = JACK_CLEAR
        if uno_usb_x - m.JACK_BODY_X[1] - c < xin:
            hood = hood.cut(box(uno_usb_x - m.JACK_BODY_X[1] - c, xin + 0.01, jy - m.JACK_W / 2 - jc, jy + m.JACK_W / 2 + jc,
                                jz - m.JACK_H / 2 - jc, jz + m.JACK_H / 2 + jc))
    x0, y0 = uno_xy(UNO_L, 0)
    if x0 - c < xin:
        hood = hood.cut(box(x0 - c, xin + 0.01, y0 - c, y0 + UNO_W + c, utop - c, uno_back_z + c))
    if uno_usb_x - 67.77 - c < xin:
        hood = hood.cut(box(uno_usb_x - 67.77 - c, xin + 0.01, uno_y0 + 8.22 - 1.0 - c, uno_y0 + 38.53 + 1.0 + c,   # + the 45 deg corners
                        shield_bot - SHIELD_PCB_T - c, shield_bot + c))
    # Apple II side vent grooves (flat bottom, 45 degree top).
    y0, y1 = y_ridge + 6, D - 6
    for i in range(VENT_N):
        zb, zt = H - VENT_TOP - i * VENT_PITCH - VENT_W / 2, H - VENT_TOP - i * VENT_PITCH + VENT_W / 2
        for sx in VENT_SIDES:
            surf, back = sx * W / 2, sx * (W / 2 - VENT_DEPTH)
            prof = [(surf + sx, zb), (back, zb), (back, zt - VENT_DEPTH), (surf + sx, zt + 1)]
            hood = hood.cut(cq.Workplane("XZ", origin=(0, y0, 0)).polyline(prof).close().extrude(-(y1 - y0)).val())
    if DECK_TEXT:
        hood = hood.cut(deck_text())
    return hood.clean()


# ---------------------------------------------------------------------------
# Tray (bottom + back)
# ---------------------------------------------------------------------------
def make_tray():
    """Bottom + back wall, T-shaped like the hood: full width under the screen, narrow behind."""
    xi = W / 2 - WALL - 0.3
    ys = step_y()
    nl, nr = XL + WALL + 0.3, XR - WALL - 0.3
    tray = box(-xi, xi, FRONT_FLOOR + 0.3, ys - WALL - 0.3, 0, BOTTOM_T)
    tray = tray.fuse(box(nl, nr, ys - WALL - 1, D, 0, BOTTOM_T))
    tray = tray.fuse(box(nl, nr, D - BACK_T, D, 0, H - WALL - 0.3))
    csk_h = (CSK_D - SCREW_CLEAR_D) / 2
    holes = [(bx, y) for bx in block_xs() for y in (FRONT_FLOOR + 6, wing_block_y())] + pillar_xys()
    for x, y in holes:
        tray = tray.cut(cq.Solid.makeCylinder(SCREW_CLEAR_D / 2, BOTTOM_T + 2, cq.Vector(x, y, -1)))
        tray = tray.cut(cq.Solid.makeCone(CSK_D / 2 + 0.5, SCREW_CLEAR_D / 2, csk_h + 0.5, cq.Vector(x, y, -0.5)))
    feet = [(sx * (W / 2 - WALL - 24), FRONT_FLOOR + 16) for sx in (-1, 1)] + \
           [(sx * (min(-nl, nr) - 9), D - BACK_T - 24) for sx in (-1, 1)]
    for x, y in feet:
        tray = tray.cut(cq.Solid.makeCylinder(FOOT_D / 2, FOOT_DEPTH + 1, cq.Vector(x, y, -1)))
    return tray.clean()


def uno_model():
    """The Uno STEP model hanging in place: turned 180 degrees about Y, its back on the standoffs."""
    ox, oy = UNO_MODEL_XY
    loc = cq.Location(cq.Vector(uno_usb_x - ox, uno_y0 + oy, uno_back_z), cq.Vector(0, 1, 0), 180)
    return cq.importers.importStep(str(UNO_STEP)).val().moved(loc)


def display_model():
    if DISPLAY_STEP.exists():
        return cq.importers.importStep(str(DISPLAY_STEP)).val().moved(BOARD_LOC)
    return None


def summary():
    return {
        "outer W x D x H (mm)": f"{W:.1f} x {D + HOOD_BACK_LIP:.1f} x {H:.1f}",
        "narrow back X (mm)": f"{XL:.2f} to {XR:.2f} ({XR - XL:.1f} wide), from Y {step_y():.1f}",
        "headphone jack front X, centre Y, Z": "%.1f, %.1f, %.1f" % jack_case_xyz(),
        "deck depth (mm)": f"{D - y_ridge:.1f}",
        "Uno front edge Y (mm)": f"{uno_y0:.1f}",
        "Uno USB edge X (mm)": f"{uno_usb_x:.1f}",
        "stack Z range (mm)": f"{stack_z0:.1f} - {uno_back_z:.1f}",
    }


if __name__ == "__main__":
    hood, tray = make_hood(), make_tray()
    for shape, name in ((hood, "hood"), (tray, "tray")):
        cq.exporters.export(cq.Workplane().add(shape), str(HERE / f"drum_case_{name}.step"))
    assy = (cq.Assembly(name="drum_case")
            .add(hood, name="hood", color=cq.Color(0.87, 0.82, 0.70))
            .add(tray, name="tray", color=cq.Color(0.70, 0.66, 0.56)))
    disp = display_model()
    if disp is not None:
        assy.add(disp, name="display_DisplayV2", color=cq.Color(0.1, 0.4, 0.2))
    if UNO_STEP.exists():
        assy.add(uno_model(), name="uno_R3", color=cq.Color(0.1, 0.35, 0.6))
    else:
        for i, part in enumerate(stack_envelope()[:2]):
            assy.add(part, name=f"uno_{i}", color=cq.Color(0.1, 0.35, 0.6, 0.6))
    for name, (part, col) in shield_parts_in_case().items():
        assy.add(part, name=f"shield_{name}".replace(" ", "_"), color=cq.Color(*col))
    assy.export(str(HERE / "drum_case_assembly.step"))
    for k, v in summary().items():
        print(f"{k:34s} {v}")
