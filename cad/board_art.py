"""Top-side artwork of a board straight from its EagleCAD .brd file, as thin coloured layers
on the board's top face: copper traces, gold pads, drill holes and white silkscreen (lines,
logos and text).

This is how ECAD tools make realistic STEP boards: STEP has no textures, so the artwork is
real geometry, coloured per layer. Text is drawn with a system font (Eagle stores text as
words, not shapes), so letters are close to the real board but not the exact typeface.

    layers = board_art("reference/boards/UNO-TH_Rev3e.brd")
    # {"copper": [faces], "pads": [...], "drills": [...], "silk": [...]}, board coordinates (mm)
    sheets = art_solids(layers, z_top=1.6)   # {"copper": Compound of faces, ...}
"""
import math
import re
import xml.etree.ElementTree as ET

import cadquery as cq

# Layer height above the board top, and thickness: paper thin, each above the last.
LAYER_Z = {"copper": (0.000, 0.030), "pads": (0.000, 0.045), "silk": (0.030, 0.050), "drills": (0.045, 0.055)}
COLOURS = {"copper": None, "pads": (0.83, 0.68, 0.30), "silk": (0.96, 0.96, 0.96), "drills": (0.10, 0.10, 0.10)}
ARC_STEPS = 10


def _rot(spec):
    """Eagle rotation like 'R90', 'MR270', 'SR45' -> (mirrored, degrees)."""
    if not spec:
        return False, 0.0
    m = re.match(r"([MS]*)R([\d.]+)", spec)
    return "M" in m.group(1), float(m.group(2))


class _Xf:
    """Package coordinates -> board coordinates for one element."""
    def __init__(self, x=0.0, y=0.0, rot=None):
        self.x, self.y = x, y
        self.mirror, deg = _rot(rot)
        self.c, self.s = math.cos(math.radians(deg)), math.sin(math.radians(deg))

    def __call__(self, px, py):
        if self.mirror:
            px = -px
        return self.x + px * self.c - py * self.s, self.y + px * self.s + py * self.c


def _face(points):
    pts = [cq.Vector(x, y, 0) for x, y in points]
    return cq.Face.makeFromWires(cq.Wire.makePolygon(pts, close=True))


def _circle_pts(cx, cy, r, n=24):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _slot(xf, x1, y1, x2, y2, w, curve=0.0):
    """A wire of width w as a polygon (round ends), arcs approximated."""
    pts = [(x1, y1), (x2, y2)]
    if curve:
        # Eagle arc from p1 to p2 sweeping `curve` degrees (counter-clockwise if positive).
        a = math.radians(curve)
        dx, dy = x2 - x1, y2 - y1
        chord = math.hypot(dx, dy)
        r = chord / (2 * math.sin(abs(a) / 2))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        h = math.sqrt(max(r * r - (chord / 2) ** 2, 0))
        sgn = 1 if curve > 0 else -1
        cx, cy = mx - sgn * h * dy / chord, my + sgn * h * dx / chord
        a0 = math.atan2(y1 - cy, x1 - cx)
        pts = [(cx + r * math.cos(a0 + a * i / ARC_STEPS), cy + r * math.sin(a0 + a * i / ARC_STEPS))
               for i in range(ARC_STEPS + 1)]
    pts = [xf(*p) for p in pts]
    faces = []
    hw = max(w, 0.05) / 2
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        if L < 1e-6:
            continue
        nx, ny = -(by - ay) / L * hw, (bx - ax) / L * hw
        faces.append(_face([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)]))
    for x, y in (pts[0], pts[-1]):      # round ends: true circles keep the STEP small
        faces.append(cq.Face.makeFromWires(cq.Wire.makeCircle(hw, cq.Vector(x, y, 0), cq.Vector(0, 0, 1))))
    return faces


def _rect(xf, x1, y1, x2, y2, rot=None):
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    hx, hy = abs(x2 - x1) / 2, abs(y2 - y1) / 2
    inner = _Xf(cx, cy, rot)
    return [_face([xf(*inner(sx * hx, sy * hy)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])]


def _ring(xf, x, y, r_out, r_in=0.0):
    cx, cy = xf(x, y)
    outer = cq.Wire.makeCircle(r_out, cq.Vector(cx, cy, 0), cq.Vector(0, 0, 1))
    if r_in <= 0:
        return [cq.Face.makeFromWires(outer)]
    inner = cq.Wire.makeCircle(r_in, cq.Vector(cx, cy, 0), cq.Vector(0, 0, 1))
    return [cq.Face.makeFromWires(outer, [inner])]


def _text(xf, txt, x, y, size, rot=None, align=None):
    if not txt or not txt.strip():
        return []
    mirror, deg = _rot(rot)
    if mirror:
        return []                                   # bottom-side text
    halign = {"center": "center", "top-center": "center", "bottom-center": "center", "center-left": "left",
              "center-right": "right", "bottom-right": "right", "top-right": "right"}.get(align, "left")
    valign = {"center": "center", "center-left": "center", "center-right": "center", "top-left": "top",
              "top-center": "top", "top-right": "top"}.get(align, "bottom")
    bx, by = xf(x, y)
    dx = xf(x + 1, y)
    total = deg + math.degrees(math.atan2(dx[1] - by, dx[0] - bx))   # text + element rotation
    # Like Eagle: text that would read upside down is turned the other way round (unless the
    # rotation is "spin", S), anchored from the opposite corner.
    if "S" not in (rot or "") and 90 < total % 360 <= 270:
        total -= 180
        halign = {"left": "right", "right": "left"}.get(halign, halign)
        valign = {"bottom": "top", "top": "bottom"}.get(valign, valign)
    out = []
    lines = txt.split("\n")
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            w = cq.Workplane("XY").text(line, size * 1.15, 0.01, font="Arial", halign=halign, valign=valign)
        except Exception:
            continue
        for f in w.faces("<Z").vals():
            f = f.translate(cq.Vector(0, (len(lines) - 1 - i) * size * 1.35, 0))   # Eagle anchors the last line
            f = f.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), total).translate(cq.Vector(bx, by, 0))
            out.append(f)
    return out


SILK = ("21",)


def _items(el_list, xf, layers, names=None):
    """Package or board items -> faces in `layers` (dict)."""
    for el in el_list:
        tag, L = el.tag, el.get("layer")
        f = lambda k, d=0.0: float(el.get(k, d))
        if tag == "smd" and L == "1":
            inner = _Xf(f("x"), f("y"), el.get("rot"))
            hx, hy = f("dx") / 2, f("dy") / 2
            layers["pads"] += [_face([xf(*inner(sx * hx, sy * hy)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])]
        elif tag == "pad":
            drill = f("drill")
            dia = f("diameter") or drill * 1.8
            if el.get("shape") in ("square", "octagon"):
                layers["pads"] += _rect(xf, f("x") - dia / 2, f("y") - dia / 2, f("x") + dia / 2, f("y") + dia / 2, el.get("rot"))
            elif el.get("shape") == "long":
                layers["pads"] += _slot(xf, f("x") - dia / 2, f("y"), f("x") + dia / 2, f("y"), dia)
            else:
                layers["pads"] += _ring(xf, f("x"), f("y"), dia / 2)
            layers["drills"] += _ring(xf, f("x"), f("y"), drill / 2)
        elif L in SILK:
            if tag == "wire":
                layers["silk"] += _slot(xf, f("x1"), f("y1"), f("x2"), f("y2"), f("width"), f("curve"))
            elif tag == "rectangle":
                layers["silk"] += _rect(xf, f("x1"), f("y1"), f("x2"), f("y2"), el.get("rot"))
            elif tag == "circle":
                r, w = f("radius"), f("width")
                layers["silk"] += _ring(xf, f("x"), f("y"), r + w / 2, max(r - w / 2, 0) if w else 0)
            elif tag == "polygon":
                pts = [(float(v.get("x")), float(v.get("y"))) for v in el.iter("vertex")]
                if len(pts) >= 3:
                    layers["silk"].append(_face([xf(*p) for p in pts]))
            elif tag == "text":
                txt = el.text or ""
                if names:
                    txt = txt.replace(">NAME", names[0]).replace(">VALUE", names[1])
                if names and el.text and el.text.startswith(">"):
                    continue                        # part names / values aren't printed
                if txt.startswith(">"):
                    continue
                layers["silk"] += _text(xf, txt, f("x"), f("y"), f("size", 1.0), el.get("rot"), el.get("align"))


def board_art(brd_path, silk_text=True, plain_silk=("21",)):
    """plain_silk: board-level layers that are printed as silkscreen (the Uno prints its
    labels from layer 25 too). Anything off the board outline is dropped."""
    global SILK
    root = ET.parse(brd_path).getroot()
    layers = {"copper": [], "pads": [], "drills": [], "silk": []}
    packages = {(lib.get("name"), p.get("name")): p for lib in root.iter("library") for p in lib.iter("package")}
    for e in root.findall(".//board/elements/element"):
        mirror, _ = _rot(e.get("rot"))
        if mirror:
            continue                                # bottom-side part
        pkg = packages.get((e.get("library"), e.get("package")))
        if pkg is None:
            continue
        xf = _Xf(float(e.get("x")), float(e.get("y")), e.get("rot"))
        items = [el for el in pkg if silk_text or el.tag != "text"]
        _items(items, xf, layers, (e.get("name"), e.get("value") or ""))
    plain = root.find(".//board/plain")
    if plain is not None:
        SILK = tuple(plain_silk)
        _items([el for el in plain if silk_text or el.tag != "text"], _Xf(), layers)
        SILK = ("21",)
        xs = [float(w.get(k)) for w in plain.iter("wire") if w.get("layer") == "20" for k in ("x1", "x2")]
        ys = [float(w.get(k)) for w in plain.iter("wire") if w.get("layer") == "20" for k in ("y1", "y2")]
        if xs:
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            def on_board(f):
                b = f.BoundingBox()
                return b.xmin >= x0 - 0.3 and b.xmax <= x1 + 0.3 and b.ymin >= y0 - 0.3 and b.ymax <= y1 + 0.3
            for k in layers:
                layers[k] = [f for f in layers[k] if on_board(f)]
    for s in root.iter("signal"):
        for el in s:
            if el.tag == "wire" and el.get("layer") == "1":
                g = lambda k: float(el.get(k, 0))
                layers["copper"] += _slot(_Xf(), g("x1"), g("y1"), g("x2"), g("y2"), g("width"), g("curve"))
            elif el.tag == "via":
                drill = float(el.get("drill"))
                dia = float(el.get("diameter", 0)) or drill + 0.6
                layers["copper"] += _ring(_Xf(), float(el.get("x")), float(el.get("y")), dia / 2)
                layers["drills"] += _ring(_Xf(), float(el.get("x")), float(el.get("y")), drill / 2)
    return layers


def _fuse(faces):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
    from OCP.TopTools import TopTools_ListOfShape
    if len(faces) < 2:
        return cq.Compound.makeCompound(faces)
    args, tools = TopTools_ListOfShape(), TopTools_ListOfShape()
    args.Append(faces[0].wrapped)
    for f in faces[1:]:
        tools.Append(f.wrapped)
    op = BRepAlgoAPI_Fuse()
    op.SetArguments(args)
    op.SetTools(tools)
    op.SetFuzzyValue(1e-5)
    op.Build()
    return cq.Shape.cast(op.Shape()).clean()


def art_solids(layers, z_top, offset=(0.0, 0.0)):
    """Faces -> one sheet (compound of faces, no thickness) per layer, each a hair above the
    one below, on a board whose top is at z_top. Sheets, not solids, and the silkscreen merged
    into one piece, keep the STEP about a tenth the size (a solid layer per board ran to
    150 MB)."""
    out = {}
    for name, faces in layers.items():
        if not faces:
            continue
        shape = _fuse(faces) if name == "silk" else cq.Compound.makeCompound(faces)
        out[name] = shape.translate(cq.Vector(offset[0], offset[1], z_top + LAYER_Z[name][1]))
    return out
