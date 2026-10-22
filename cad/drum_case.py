"""Parametric sloped console case for the drum player (was the coffee player case): Ender-3 V2 DWIN display + Arduino Uno
with an Adafruit Music Maker.

Style: classic sloped console (vertical front lip, 30 degree screen face, flat rear deck)
with Apple II side vent grooves. Two printed parts:

  hood          - sides, front lip, sloped screen face, deck and back wall in one piece, so it
                  can stand on its flat back. The display board goes in through the open
                  bottom and screws to posts behind the screen window; the Uno stack hangs
                  upside down from the deck on long gusseted standoffs, its plugs at holes in
                  the back wall.
  bottom cover  - a flat plate held by 4 countersunk screws up into blocks in the hood. It
                  comes off without touching any wiring.

Coordinates (mm): X = width (centred), Y = depth (front face at Y=0, back at Y=D),
Z = up (bottom at Z=0). Everything is exported in its assembled position.

Run:  python console_case.py
"""
import math
from pathlib import Path

import cadquery as cq
from OCP.gp import gp_Trsf

HERE = Path(__file__).resolve().parent
def _first(*paths):
    """The first of these paths that exists (the repo layout, then the mini-4560 one), else the first."""
    return next((p for p in paths if p.exists()), paths[0])


DISPLAY_STEP = _first(HERE / "reference" / "DisplayV2.step", HERE.parent / "ender 3 v2 models" / "DisplayV2.step")
UNO_STEP = _first(HERE / "reference" / "arduino_uno_r3.step", HERE.parent.parent / "STEP files" / "ARDUINO UNO R3 Step.STEP")   # mikeoverbay's Uno model: visuals only, its holes are wrong
# Everything this script makes goes in generated/, so it never overwrites mikeoverbay's
# hand-edited hood (Shapr3D) next to it, which is the one to print.
OUT_DIR = HERE / "generated"
STL_DIR = OUT_DIR
# (In the repo, cad/stl holds mikeoverbay's Shapr3D-edited STLs, so the script must not write there.)
UNO_MODEL_XY = (33.04, 27.26)   # add to the model's x, y to get Uno coordinates (matched on its 4 holes)

# ---------------------------------------------------------------------------
# Display: Ender-3 V2 DWIN board (from DisplayV2.step). Board coordinates: front (LCD)
# side facing you, knob on the right, origin at the bottom-left corner, z=0 = PCB top.
# ---------------------------------------------------------------------------
BOARD_W, BOARD_H, BOARD_T = 141.0, 74.0, 1.7
# Corner holes: caliper spacing 114.9 x 66.2, kept centred where DisplayV2 puts the pattern.
# The 5th hole (beside the knob): in line with the knob, 26.0 from the bottom edge (caliper).
_hx, _hy = (60.95, 57.46), (36.95, 33.10)
KNOB_X = 138.41 - 6.0                    # caliper: left edge to far side of the 12 mm encoder, less half
BOARD_HOLES = [(_hx[0] - _hx[1], _hy[0] - _hy[1]), (_hx[0] - _hx[1], _hy[0] + _hy[1]),
               (_hx[0] + _hx[1], _hy[0] - _hy[1]), (_hx[0] + _hx[1], _hy[0] + _hy[1]), (KNOB_X, 26.0)]
BOARD_HOLE_D = 3.0                       # caliper 3.0-3.1 -> M2.5 screws
LCD = (8.0, 114.0, 3.0, 71.0)            # LCD module outline x0, x1, y0, y1
LCD_H = 5.2                              # LCD front face above the PCB top
VA = (12.2, 109.9, 11.2, 67.7)           # visible screen area (DisplayV2)
ENC = (KNOB_X, 39.0)                     # knob centre: x by caliper,
                                         # level with the screen centre (DisplayV2 + Creality housing)
ENC_BODY, ENC_BODY_H = 12.0, 6.6
ENC_SHAFT_D, ENC_SHAFT_TOP = 6.7, 21.21  # caliper: board to top of shaft
# Parts on the back: x0, x1, y0, y1, depth below the PCB bottom
BACK_PARTS = [
    (15.2, 24.4, 20.0, 40.7, 9.6),       # 2x5 ribbon header
    (120.6, 129.8, 52.0, 61.2, 5.6),     # buzzer
    (30.0, 37.0, 51.1, 58.1, 5.4),       # capacitor
    (50.6, 57.6, 51.1, 58.1, 5.4),       # capacitor
    (26.3, 49.9, 39.7, 45.5, 1.8),       # LCD flex connector
    (30.0, 45.0, 7.0, 22.2, 1.8),        # SD socket
]
HEADER = BACK_PARTS[0]
RIBBON_PLUG = 8.0                        # ribbon plug + cable bend beyond the header shroud

# ---------------------------------------------------------------------------
# Electronics stack: Arduino Uno R3 + Adafruit Music Maker plugged straight on, hanging
# upside down from the deck (easier wiring), USB toward the back
# ---------------------------------------------------------------------------
UNO_L, UNO_W = 68.58, 53.34
# x from the USB edge, y from the power-header edge. The hole beside the power jack is from
# Arduino's official UNO R3 holes (UNO-TH_Rev3e.brd, docs.arduino.cc/hardware/uno-rev3).
# mikeoverbay's Uno STEP model has the first one wrong at (15.24, 3.71).
UNO_HOLES = [(13.97, 2.54), (15.24, 50.80), (66.04, 7.62), (66.04, 35.56)]
UNO_PCB_T = 1.6
UNO_USB_OVERHANG = 6.35
# Plugs on the stack's back edge that get a hole in the back wall: (u from the power-header
# edge, h above the Uno's component side, hole w, hole h; h = 0 for a round hole of diameter w).
# Scaled from mikeoverbay's photo of the stack, then corrected by their checks against the real
# stack: 3.22 mm left and 0.95 mm down, seen from the back, then 0.68 mm back right so the USB
# socket's left side is 84.04 mm from the hood's inside left wall (caliper). The holes leave
# room for the plug bodies, since the wall is 3.5 mm out from the sockets.
# USB-B socket: 11.8 wide centred 38.10 from the power-header edge (Arduino's UNO R3 file,
# confirmed by caliper: 9.33 vs 9.34 from the far edge), about 11.0 tall on the Uno's board.
# Headphone jack nose: 5.0 dia, axis 26.16 from the power-header edge (Adafruit's board file,
# music_maker_shield.py) and MM_GAP + 1.6 board + 2.5 axis (typical) = 15.4 above the Uno.
USB_SOCKET = (38.10, 5.5, 11.8, 11.0)    # u, h above the Uno's component side (centre), w, h
HEADPHONE_NOSE = (26.16, 15.4, 5.0)      # u, h, diameter
USB_GROW = 1.5        # the USB hole is the socket plus this all round (mikeoverbay)
HEADPHONE_GROW = 3.0  # the headphone hole is the jack nose plus this on the diameter, for the plug
BACK_PLUGS = {
    "Uno USB": (USB_SOCKET[0], USB_SOCKET[1], USB_SOCKET[2] + 2 * USB_GROW, USB_SOCKET[3] + 2 * USB_GROW),
    "Music Maker headphone": (HEADPHONE_NOSE[0], HEADPHONE_NOSE[1], HEADPHONE_NOSE[2] + HEADPHONE_GROW, 0.0),
}
# Two 1/4" (6.35 mm) panel jacks on the back wall, either side of the plug holes.
JACK_D = 9.8               # Switchcraft-style open-frame jack: 3/8"-32 bushing (9.53) + print allowance
JACK_XS = (-50.0,)         # centre across the back: the USB side, so the audio wires from the
                           # Music Maker's jack don't cross the boards (mikeoverbay)
JACK_Z = 30.0              # centre height
JACK_BODY = (20.0, 20.0, 35.0)   # keep-out behind the wall for an open-frame jack: w, h, depth
HOLE_CHAMFER = 0.8         # 45 degree chamfer on the outside edge of every back wall hole (mikeoverbay)
STANDOFF_D, PILOT_D = 9.0, 2.5
STANDOFF_FLAT = 2.5    # D-shaped standoffs: flat this far from the hole, on the side facing the Uno's centre
HANG_PILOT = 5.8       # standoff pilot depth, up from the end: 3 x 6 mm screws
STACK_BODY_H = 24.0    # Uno underside to the top of the Music Maker's screw terminals, no standoffs
                       # (23.6 scaled from the photo; add ~12.5 per extra shield)
UNO_X = 0.0            # stack centre across the case
UNO_FLOOR_H = 40.0     # the standoff ends (the Uno's back) this far above the inside of the floor
UNO_SOLDER = 2.0       # pins and solder on the Uno's back, which faces the deck
RIB_T = 3.0            # standoffs: 45 degree gussets up to the deck, this thick
RIB_CLEAR = 1.0        # gussets start at least this far above the Uno's solder side
RIB_REACH = 12.0       # and reach at most this far down the standoff (and out along the deck)
MM_GAP = 11.3          # Uno's component side to the Music Maker's board (photo)
SLOPE_CLEAR = 1.0      # Uno's back to the inside of the slope

# ---------------------------------------------------------------------------
# Case
# ---------------------------------------------------------------------------
TILT = 30.0            # screen face angle up from the desk
WALL = 3.0             # also the screen face thickness
BOTTOM_T = 3.0         # bottom cover and hood front floor strip
BACK_T = 3.0           # back wall
ELEPHANT_FOOT = 0.6    # 45 degree chamfer round the back face's outside edge: the hood prints
                       # standing on its back, and this hides the first layer's squish
FRONT_FLOOR = 15.0     # hood floor strip behind the front lip
FRONT_H_MIN = 15.0     # front lip height (raised automatically if the ribbon plug needs it)
D_MIN = 120.0          # depth (raised automatically to fit the Uno stack behind the display)
SCREEN_MARGIN = 14.05  # slope face beyond the board on each side; sets the width and slope length
LCD_GAP = 0.2          # LCD face to the back of the screen face
WINDOW_INSET = -0.4    # screen window inside (+) / beyond (-) the visible area, per side
WINDOW_CHAMFER = 1.2
KNOB_HOLE_D = ENC_SHAFT_D + 2.8   # 1.4 mm all round; hidden under the knob
ENC_POCKET = ENC_BODY + 5.0      # encoder body pocket behind the face: 17 x 17, 2.5 mm round the body
ENC_POCKET_CLEAR = 0.9           # pocket depth beyond the encoder body: 2.1 mm deep, 0.9 mm of face left
BOSS_D = 7.0
BOARD_PILOT_D = 2.1              # M2.5 self-tapping screws through the 3.0 mm board holes
FLOOR_CLEAR = 2.0      # minimum gap between display parts and the floor
STACK_CLEAR = 3.0      # minimum gap between the stack and the display
PATH_CLEAR = 1.0       # minimum gap between the standoffs and the screen on its way in or out
R_SIDE, R_RIDGE, R_LIP = 4.0, 6.0, 3.0   # R_SIDE also rounds the back corners and the deck-to-back
                                         # edge (mikeoverbay: "radius the back edge"); bottom edges stay sharp
CSK_D, SCREW_CLEAR_D = 6.3, 3.4  # countersunk bottom-cover screws
BLOCK = 10.0           # bottom-cover screw blocks inside the hood
SCREW_L = 14.0         # 3 x 14 countersunk wood screws up through the bottom cover
PILOT_CHAMFER = 0.8    # 45 degree lead-in on the screw pilots
BLOCK_H = SCREW_L - 3.0 + 2.0   # the screw goes 11 mm into the block, plus 2 mm of plastic
# Apple II side vent grooves
VENT_N, VENT_PITCH, VENT_W, VENT_DEPTH, VENT_TOP = 6, 3.5, 1.6, 1.0, 9.0
FOOT_D, FOOT_DEPTH = 10.0, 1.0

# ---------------------------------------------------------------------------
# Derived geometry
# ---------------------------------------------------------------------------
T = math.radians(TILT)
sinT, cosT, tanT = math.sin(T), math.cos(T), math.tan(T)
X = cq.Vector(1, 0, 0)
U = cq.Vector(0, cosT, sinT)             # up the slope
N = cq.Vector(0, -sinT, cosT)            # slope outward normal

W = BOARD_W + 2 * SCREEN_MARGIN
L_slope = BOARD_H + 2 * SCREEN_MARGIN
s_c = L_slope / 2                        # board centre, along the slope from the lip top
pcb_depth = WALL + LCD_GAP + LCD_H       # PCB top below the slope surface


def board_sd(bx, by, bz):
    """Board coordinates -> (s, d) on the slope (bz up from the PCB top towards the LCD)."""
    return s_c + by - BOARD_H / 2, pcb_depth - bz


hx0, hx1, hy0, hy1, hdep = HEADER


def underside_parts():
    """Board-side keep-outs as (x0, x1, y0, y1, depth of the underside below the slope surface)."""
    parts = [(0, BOARD_W, 0, BOARD_H, pcb_depth + BOARD_T)]
    for x0, x1, y0, y1, dep in BACK_PARTS:
        parts.append((x0, x1, y0, y1, pcb_depth + BOARD_T + dep))
    parts.append((hx0 - 1, hx1 + 1, hy0 - 1, hy1 + 1, pcb_depth + BOARD_T + hdep + RIBBON_PLUG))
    return parts


# Front lip height: the lowest display part (the ribbon plug) must clear the floor.
FRONT_H = max([FRONT_H_MIN] + [BOTTOM_T + FLOOR_CLEAR - (board_sd(0, y0, 0)[0] * sinT - d * cosT)
                               for _, _, y0, _, d in underside_parts()])
H = FRONT_H + L_slope * sinT
y_ridge = L_slope * cosT
# Long standoffs bring the hanging stack down near the floor.
STANDOFF_H = H - WALL - BOTTOM_T - UNO_FLOOR_H
if STANDOFF_H < 5.0 or UNO_FLOOR_H - STACK_BODY_H < 1.0:
    raise ValueError(f"UNO_FLOOR_H {UNO_FLOOR_H}: standoffs {STANDOFF_H:.1f} mm, stack bottom "
                     f"{UNO_FLOOR_H - STACK_BODY_H:.1f} mm above the floor")
STACK_H = STANDOFF_H + STACK_BODY_H      # stack including its standoffs
uno_back_z = H - WALL - STANDOFF_H       # the Uno's back (solder side), against the standoff ends


# Screen face plane: on the slope surface, origin at the board centre.
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


def stack_z_range():
    """Z range of the Uno stack, standoffs included."""
    return H - WALL - STACK_H, H - WALL


def stack_y_front_min():
    """Smallest Y for the stack's front face that clears every display part, keeps the
    standoffs clear of the screen's way out, and keeps the Uno's back clear of the inside of
    the slope."""
    z0, z1 = stack_z_range()
    ahead = STANDOFF_D / 2 - (UNO_L - UNO_HOLES[2][0])  # front standoffs reach this far past the Uno
    keep = cq.Compound.makeCompound(display_keepout())
    # The screen comes out back and down (-N), past the standoffs, with the ribbon unplugged.
    parts = display_keepout()[:-1] + [
        cq.Solid.makeCylinder(ENC_SHAFT_D / 2, ENC_SHAFT_TOP, cq.Vector(*ENC, 0)).moved(BOARD_LOC)]
    path = cq.Compound.makeCompound([p.moved(cq.Location(-N * t)) for p in parts for t in range(1, 31)])
    lo, hi = 0.0, 250.0
    for _ in range(30):
        mid = (lo + hi) / 2
        x0, x1 = UNO_X - UNO_W / 2, UNO_X + UNO_W / 2
        body = box(x0, x1, mid, mid + UNO_L + UNO_USB_OVERHANG, z0, uno_back_z + UNO_SOLDER)
        posts = box(x0 - ahead, x1 + ahead, mid - ahead, mid + UNO_L, uno_back_z, z1)
        ok = (min(body.distance(keep), posts.distance(keep)) >= STACK_CLEAR
              and posts.distance(path) >= PATH_CLEAR)
        lo, hi = (lo, mid) if ok else (mid, hi)
    return max(hi, (uno_back_z + UNO_SOLDER + SLOPE_CLEAR - FRONT_H + WALL / cosT) / tanT)


stack_front = stack_y_front_min()
D = max(D_MIN, stack_front + UNO_L + UNO_USB_OVERHANG + 0.5 + BACK_T)
uno_edge = D - BACK_T - 0.5 - UNO_USB_OVERHANG        # Y of the Uno's USB-side board edge


def rounded_rect(w, h, r):
    return cq.Sketch().rect(w, h).vertices().fillet(r) if r > 0 else cq.Sketch().rect(w, h)


def plane_prism(plane, cx, cy, w, h, depth, r=0.0, start=0.0):
    """Rounded rectangle on a plane, extruded `depth` into the case (against the normal)."""
    wp = cq.Workplane(plane).workplane(offset=-start).center(cx, cy)
    return wp.placeSketch(rounded_rect(w, h, r)).extrude(-depth).val()


def plane_cyl(plane, cx, cy, dia, depth, start=0.0):
    p = plane.toWorldCoords((cx, cy, -start))
    return cq.Solid.makeCylinder(dia / 2, depth, p, -plane.zDir)


def face_xy(bx, by):
    """Board coordinates -> screen-face coordinates (origin at the board centre)."""
    return bx - BOARD_W / 2, by - BOARD_H / 2


# ---------------------------------------------------------------------------
# Uno stack placement
# ---------------------------------------------------------------------------
def uno_xy(ux, uy):
    """Uno coordinates (x from the USB edge, y from the power-header edge) -> case X, Y.
    Hanging upside down mirrors it across X; the USB still faces the back."""
    return UNO_X - (uy - UNO_W / 2), uno_edge - ux


def uno_standoffs():
    """D-shaped standoffs hanging from the deck at the Uno's holes (flat facing its centre),
    and their pilots, up from the free end; above the pilot each standoff is solid to the deck."""
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
        pilots.append(cq.Solid.makeCylinder(PILOT_D / 2, HANG_PILOT + 0.01, cq.Vector(x, y, zb - 0.01)))
    return bosses, pilots


def standoff_ribs():
    """Gussets from each standoff to the underside of the deck, in +-X and +-Y: triangles with
    a 45 degree underside, so they print deck-down without support. They start RIB_CLEAR above
    the Uno's solder side. A rib that would come within STACK_CLEAR of the screen's parts is
    left out."""
    zd = H - WALL                                        # underside of the deck
    h = min(STANDOFF_H - UNO_SOLDER - RIB_CLEAR, RIB_REACH)
    z_lo = zd - h                                        # rib bottom at the standoff
    if h <= 0:
        return []
    r = STANDOFF_D / 2
    prof = [(0, z_lo), (r, z_lo), (r + h, zd), (r + h, zd + 0.5), (0, zd + 0.5)]
    keep = cq.Compound.makeCompound(display_keepout())
    ribs = []
    for ux, uy in UNO_HOLES:
        x, y = uno_xy(ux, uy)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            plane = cq.Plane(origin=(x, y, 0), xDir=(dx, dy, 0), normal=(dy, -dx, 0))
            rib = cq.Workplane(plane).polyline(prof).close().extrude(RIB_T / 2, both=True).val()
            if rib.distance(keep) >= STACK_CLEAR:
                ribs.append(rib)
    return ribs


def plug_holes():
    """BACK_PLUGS -> {name: (X, Z, w, h)} on the back wall. The stack is upside down and
    mirrored across X, so the plugs sit below the Uno's board."""
    return {name: (UNO_X - (u - UNO_W / 2), uno_back_z - UNO_PCB_T - h_up, w, h)
            for name, (u, h_up, w, h) in BACK_PLUGS.items()}


# ---------------------------------------------------------------------------
# Hood
# ---------------------------------------------------------------------------
def outer_solid():
    prof = [(0, 0), (0, FRONT_H), (y_ridge, H), (D, H), (D, 0)]
    s = cq.Workplane("YZ").polyline(prof).close().extrude(W / 2, both=True).val()
    for pt, r in (((0, y_ridge, H), R_RIDGE), ((0, 0, FRONT_H), R_LIP)):
        e = min(s.Edges(), key=lambda e: (e.Center() - cq.Vector(*pt)).Length)
        s = s.fillet(r, [e])
    # R_SIDE on the side edges, the back corners and the deck-to-back edge; the bottom edges
    # stay sharp (it sits on the desk).
    edges = [e for f in s.Faces() if abs(f.normalAt().x) > 0.99
             for e in f.Edges() if e.BoundingBox().zmax > 0.01]
    edges.append(min(s.Edges(), key=lambda e: (e.Center() - cq.Vector(0, D, H)).Length))
    return s.fillet(R_SIDE, edges)


def cavity():
    z_in = lambda y: FRONT_H + y * tanT - WALL / cosT
    y_ri = (H - WALL - FRONT_H + WALL / cosT) / tanT
    y_back = D - BACK_T
    prof = [(WALL, BOTTOM_T), (WALL, z_in(WALL)), (y_ri, H - WALL), (y_back, H - WALL),
            (y_back, -1), (FRONT_FLOOR, -1), (FRONT_FLOOR, BOTTOM_T)]
    return cq.Workplane("YZ").polyline(prof).close().extrude(W / 2 - WALL, both=True).val()


def block_xs():
    return [sx * (W / 2 - WALL - BLOCK / 2) for sx in (-1, 1)]


def cover_screw_xys():
    """Bottom-cover screws: 2 behind the front lip, and 2 in the back corners, BLOCK / 2 in from
    the side and back walls."""
    return [(bx, FRONT_FLOOR + 6) for bx in block_xs()] + [(bx, D - BACK_T - BLOCK / 2) for bx in block_xs()]


def wedge_block(cx, y0, y1):
    """Bottom-cover screw block against a side wall (from the drum case): tallest at the wall,
    its free top sloping 45 degrees down and away from it, so it prints without support."""
    side = 1 if cx > 0 else -1
    xw, xin = cx + side * BLOCK / 2, cx - side * BLOCK / 2
    lift = PILOT_D / 2 + 0.75           # so the slope stays 1 mm over the pilot's top on its low side too
    z0, zw, zi = BOTTOM_T, BOTTOM_T + BLOCK_H + lift + BLOCK / 2, BOTTOM_T + BLOCK_H + lift - BLOCK / 2
    prof = [(xin, z0), (xw + 0.5 * side, z0), (xw + 0.5 * side, zw + 0.5), (xw, zw + 0.5), (xw, zw), (xin, zi)]
    return cq.Workplane("XZ", origin=(0, y0, 0)).polyline(prof).close().extrude(-(y1 - y0)).val()


def screw_pilot(x, y):
    """Blind pilot up into a block, with a 45 degree lead-in chamfer where the screw enters."""
    c = PILOT_CHAMFER
    return cq.Solid.makeCylinder(PILOT_D / 2, BLOCK_H - 1.0, cq.Vector(x, y, BOTTOM_T - 0.01)).fuse(
        cq.Solid.makeCone(PILOT_D / 2 + c, PILOT_D / 2, c + 0.01, cq.Vector(x, y, BOTTOM_T - 0.01)))


def uno_to_wall(u, h_up):
    """Uno-side position (u from the power-header edge, h above its component side) -> back wall X, Z."""
    return UNO_X - (u - UNO_W / 2), uno_back_z - UNO_PCB_T - h_up


def back_wall_holes():
    """Plug holes and 1/4\" jack holes through the back wall, each with a HOLE_CHAMFER 45 degree
    chamfer on its outside edge. The inside face stays flat for the jack frames."""
    c = HOLE_CHAMFER
    rounds = [(x, z, w / 2) for x, z, w, h in plug_holes().values() if not h] + [(jx, JACK_Z, JACK_D / 2) for jx in JACK_XS]
    holes = []
    for x, z, w, h in plug_holes().values():
        if h:
            r = 1.5
            holes.append(cq.Workplane("XZ", origin=(x, D + 1, z)).rect(w, h).extrude(BACK_T + 2).edges("|Y").fillet(r).val())
            holes.append(cq.Workplane("XZ", origin=(x, D + 0.01, z))
                         .placeSketch(rounded_rect(w + 2 * c + 0.02, h + 2 * c + 0.02, r + c + 0.01),
                                      rounded_rect(w, h, r).moved(cq.Location(cq.Vector(0, 0, c + 0.01))))
                         .loft().val())
    for x, z, r in rounds:
        holes.append(cq.Solid.makeCylinder(r, BACK_T + 2, cq.Vector(x, D + 1, z), cq.Vector(0, -1, 0)))
        holes.append(cq.Solid.makeCone(r + c + 0.01, r, c + 0.01, cq.Vector(x, D + 0.01, z), cq.Vector(0, -1, 0)))
    return holes


def screen_features(hood):
    """Screen window, knob hole, encoder pocket and board posts in the sloped face."""
    P = face_plane
    # Screen window with a chamfer on the front.
    wx, wy = face_xy((VA[0] + VA[1]) / 2, (VA[2] + VA[3]) / 2)
    ww, wh = VA[1] - VA[0] - 2 * WINDOW_INSET, VA[3] - VA[2] - 2 * WINDOW_INSET
    hood = hood.cut(plane_prism(P, wx, wy, ww, wh, WALL + 2, 0.5, start=-1))
    c = WINDOW_CHAMFER
    cham = (cq.Workplane(P).workplane(offset=0.01).center(wx, wy).rect(ww + 2 * c + 0.02, wh + 2 * c + 0.02)
            .workplane(offset=-(c + 0.01)).rect(ww, wh).loft().val())
    hood = hood.cut(cham)
    # Knob shaft hole and a pocket for the encoder body behind the face.
    kx, ky = face_xy(*ENC)
    hood = hood.cut(plane_cyl(P, kx, ky, KNOB_HOLE_D, WALL + 2, start=-1))
    pocket = ENC_BODY_H - (LCD_GAP + LCD_H) + ENC_POCKET_CLEAR
    hood = hood.cut(plane_prism(P, kx, ky, ENC_POCKET, ENC_POCKET, pocket + 0.01, 0.5, start=WALL - pocket))
    # Board posts: from the back of the face to the PCB top, pilots for M2.5 self-tappers.
    boss_len = LCD_GAP + LCD_H
    for hx, hy in BOARD_HOLES:
        bx, by = face_xy(hx, hy)
        hood = hood.fuse(plane_cyl(P, bx, by, BOSS_D, boss_len + 0.01, start=WALL - 0.01))
        hood = hood.cut(plane_cyl(P, bx, by, BOARD_PILOT_D, boss_len + WALL - 1.5, start=1.5))
    return hood


def make_hood():
    outer = outer_solid()
    hood = screen_features(outer.cut(cavity()))
    # Front bottom-cover screw blocks: trapezoids against the front lip, sloped back face.
    for bx in block_xs():
        prof = [(WALL - 0.5, BOTTOM_T), (FRONT_FLOOR + 16, BOTTOM_T), (FRONT_FLOOR + 6, BOTTOM_T + BLOCK_H),
                (WALL - 0.5, BOTTOM_T + BLOCK_H)]
        blk = (cq.Workplane("YZ", origin=(bx, 0, 0)).polyline(prof).close()
               .extrude(BLOCK / 2, both=True).val())
        hood = hood.fuse(blk.intersect(outer))
        hood = hood.cut(screw_pilot(bx, FRONT_FLOOR + 6))
    # Back-corner bottom-cover screw blocks at floor level, joined to the side and back walls,
    # with 45 degree undersides.
    for px, py in cover_screw_xys()[2:]:
        hood = hood.fuse(wedge_block(px, py - BLOCK / 2, py + BLOCK / 2 + 0.5).intersect(outer))
        hood = hood.cut(screw_pilot(px, py))
    # Plug and 1/4" jack holes in the back wall.
    for hole in back_wall_holes():
        hood = hood.cut(hole)
    # Uno standoffs and their gussets, clipped to the shell (the front pair would poke through
    # the slope just ahead of the ridge).
    bosses, pilots = uno_standoffs()
    for b in bosses + standoff_ribs():
        hood = hood.fuse(b.intersect(outer))
    for p in pilots:
        hood = hood.cut(p)
    # Apple II side vent grooves along the rear of both sides. Flat bottom, 45 degree top so
    # they print upright without support.
    y0, y1 = y_ridge + 6, D - 6
    for i in range(VENT_N):
        zb, zt = H - VENT_TOP - i * VENT_PITCH - VENT_W / 2, H - VENT_TOP - i * VENT_PITCH + VENT_W / 2
        for sx in (-1, 1):
            surf, back = sx * W / 2, sx * (W / 2 - VENT_DEPTH)
            prof = [(surf + sx, zb), (back, zb), (back, zt - VENT_DEPTH), (surf + sx, zt + 1)]
            groove = (cq.Workplane("XZ", origin=(0, y0, 0)).polyline(prof).close()
                      .extrude(-(y1 - y0)).val())
            hood = hood.cut(groove)
    hood = hood.clean()
    # Elephant's foot: chamfer the outline of the face the hood prints on (the back).
    # The plug holes in it already have their own chamfers.
    rim = cq.Workplane().add(hood).faces(">Y").val().outerWire().Edges()
    return hood.chamfer(ELEPHANT_FOOT, None, rim).clean()


# ---------------------------------------------------------------------------
# Bottom cover
# ---------------------------------------------------------------------------
def make_bottom_cover():
    """A floor plate inside the hood's walls, screwed up into the hood's four blocks."""
    xi = W / 2 - WALL - 0.3
    cover = box(-xi, xi, FRONT_FLOOR + 0.3, D - BACK_T - 0.3, 0, BOTTOM_T)
    csk_h = (CSK_D - SCREW_CLEAR_D) / 2
    for x, y in cover_screw_xys():
        cover = cover.cut(cq.Solid.makeCylinder(SCREW_CLEAR_D / 2, BOTTOM_T + 2, cq.Vector(x, y, -1)))
        cover = cover.cut(cq.Solid.makeCone(CSK_D / 2 + 0.5, SCREW_CLEAR_D / 2, csk_h + 0.5, cq.Vector(x, y, -0.5)))
    # Rubber feet recesses underneath.
    for sx in (-1, 1):
        for y in (FRONT_FLOOR + 16, D - 14):
            cover = cover.cut(cq.Solid.makeCylinder(FOOT_D / 2, FOOT_DEPTH + 1,
                                                    cq.Vector(sx * (W / 2 - WALL - 14), y, -1)))
    return cover.clean()


# ---------------------------------------------------------------------------
# Reference parts for fit checks (not printed)
# ---------------------------------------------------------------------------
def display_model():
    if DISPLAY_STEP.exists():
        return cq.importers.importStep(str(DISPLAY_STEP)).val().moved(BOARD_LOC)
    return None


def uno_model():
    """The Uno STEP model on its standoffs, placed by its mounting holes: component side down
    (turned over about the case's Y axis)."""
    if not UNO_STEP.exists():
        return None
    ox, oy = UNO_MODEL_XY
    t = gp_Trsf()
    t.SetValues(0, -1, 0, UNO_X - (oy - UNO_W / 2), -1, 0, 0, uno_edge - ox, 0, 0, -1, uno_back_z)
    return cq.importers.importStep(str(UNO_STEP)).val().moved(cq.Location(t))


def music_maker_model():
    """The Music Maker (amp version) from music_maker_shield.py, plugged on the hanging Uno:
    turned over and mirrored like the Uno, its board MM_GAP below the Uno's component side.
    None if music_maker_shield.py isn't next to this file."""
    try:
        import music_maker_shield as mm
    except ImportError:
        return None
    t = gp_Trsf()
    t.SetValues(0, -1, 0, UNO_X + UNO_W / 2, -1, 0, 0, uno_edge, 0, 0, -1, uno_back_z - UNO_PCB_T - MM_GAP)
    return mm, mm.shield_solid().moved(cq.Location(t))


def music_maker_envelope():
    """Placeholder for the Music Maker (no model): its board and parts, over the Uno's footprint."""
    x0, y0 = uno_xy(UNO_L, 0)
    x1, y1 = uno_xy(0, UNO_W)
    z0, _ = stack_z_range()
    return box(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), z0, uno_back_z - UNO_PCB_T - MM_GAP)


def stack_envelope():
    """Uno stack placeholder. It stops at the Uno's back (the standoffs belong to the hood)."""
    x0, y0 = uno_xy(UNO_L, 0)
    x1, y1 = uno_xy(-UNO_USB_OVERHANG, UNO_W)
    z0, _ = stack_z_range()
    return box(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), z0, uno_back_z)


def jack_bodies():
    """Keep-out boxes for the 1/4" jack bodies behind the back wall."""
    w, h, dep = JACK_BODY
    return [box(jx - w / 2, jx + w / 2, D - BACK_T - dep, D - BACK_T, JACK_Z - h / 2, JACK_Z + h / 2)
            for jx in JACK_XS]


def summary():
    return {
        "outer W x D x H (mm)": f"{W:.1f} x {D:.1f} x {H:.1f}",
        "front lip height (mm)": f"{FRONT_H:.1f}",
        "slope length / ridge Y (mm)": f"{L_slope:.1f} / {y_ridge:.1f}",
        "deck depth (mm)": f"{D - y_ridge:.1f}",
        "stack front Y (mm)": f"{uno_edge - UNO_L:.1f} (needs >= {stack_front:.1f})",
        "stack Z / standoff height (mm)": "{:.1f}-{:.1f} / {:.1f}".format(*stack_z_range(), STANDOFF_H),
        **{f"{n} hole X, Z (mm)": f"{x:.1f}, {z:.1f}" for n, (x, z, _, _) in plug_holes().items()},
    }


if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)
    hood, cover = make_hood(), make_bottom_cover()
    for shape, name in ((hood, "hood"), (cover, "bottom_cover")):
        cq.exporters.export(cq.Workplane().add(shape), str(OUT_DIR / f"drum_case_{name}.step"))
        if STL_DIR.is_dir():
            cq.exporters.export(cq.Workplane().add(shape), str(STL_DIR / f"drum_case_{name}.stl"),
                                tolerance=0.01, angularTolerance=0.1)
    assy = (cq.Assembly(name="drum_case")
            .add(hood, name="hood", color=cq.Color(0.87, 0.82, 0.70))
            .add(cover, name="bottom_cover", color=cq.Color(0.70, 0.66, 0.56)))
    disp = display_model()
    if disp is not None:
        assy.add(disp, name="display_DisplayV2", color=cq.Color(0.1, 0.4, 0.2))
    uno = uno_model()
    if uno is not None:
        assy.add(uno, name="arduino_uno", color=cq.Color(0.1, 0.35, 0.6))
        mm_model = music_maker_model()
        if mm_model is not None:
            mm, shield = mm_model
            assy.add(shield, name="music_maker_amp", color=cq.Color(0.10, 0.25, 0.65))
            # How the real jack lines up with the back wall's headphone hole, and any clash.
            jx = UNO_X - (mm.JACK_Y - UNO_W / 2)
            jz = uno_back_z - UNO_PCB_T - MM_GAP - (mm.PCB_T + mm.JACK_AXIS_Z)
            ox, oz = uno_to_wall(*HEADPHONE_NOSE[:2])
            print(f"{'Music Maker jack axis X, Z (mm)':30} {jx:.1f}, {jz:.1f}  "
                  f"(headphone hole centre {ox:.1f}, {oz:.1f}: off by {jx - ox:+.1f}, {jz - oz:+.1f})")
            clash = shield.intersect(hood).Volume()
            print(f"{'Music Maker vs hood overlap':30} {clash:.2f} mm3")
        else:
            assy.add(music_maker_envelope(), name="music_maker_envelope", color=cq.Color(0.2, 0.4, 0.8, 0.4))
    else:
        assy.add(stack_envelope(), name="uno_stack_envelope", color=cq.Color(0.2, 0.4, 0.8, 0.4))
    for i, jb in enumerate(jack_bodies()):
        assy.add(jb, name=f"jack_body_{i + 1}", color=cq.Color(0.3, 0.3, 0.3, 0.5))
    assy.export(str(OUT_DIR / "drum_case_assembly.step"))
    for k, v in summary().items():
        print(f"{k:30s} {v}")
