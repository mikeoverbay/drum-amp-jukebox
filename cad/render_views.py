"""Shaded PNG views of the drum case for the README and for quick looks.

Run after drum_case.py:  python render_views.py
Writes drumcase_front.png, drumcase_back.png, drumcase_under.png and drumcase_assembly.png.
"""
from pathlib import Path

import cadquery as cq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = Path(__file__).resolve().parent
LIGHT = np.array([0.4, -0.6, 0.7])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def mesh(shape, tol=0.2):
    verts, tris = shape.tessellate(tol, 0.3)
    v = np.array([(p.x, p.y, p.z) for p in verts])
    return v[np.array(tris)]


def shaded(tris, rgb):
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    k = 0.35 + 0.65 * np.clip(np.abs(n @ LIGHT), 0, 1)
    return np.clip(np.outer(k, rgb), 0, 1)


def render(parts, elev, azim, out):
    fig = plt.figure(figsize=(9, 7), dpi=110)
    ax = fig.add_subplot(projection="3d")
    lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
    for shape, rgb in parts:
        t = mesh(shape)
        ax.add_collection3d(Poly3DCollection(t, facecolors=shaded(t, np.array(rgb)), edgecolors="none"))
        pts = t.reshape(-1, 3)
        lo, hi = np.minimum(lo, pts.min(0)), np.maximum(hi, pts.max(0))
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(tuple(hi - lo), zoom=0.95)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(HERE / out, facecolor="white", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    hood = cq.importers.importStep(str(HERE / "drum_case_hood.step")).val()
    cover = cq.importers.importStep(str(HERE / "drum_case_bottom_cover.step")).val()
    tan, grey = (0.87, 0.82, 0.70), (0.70, 0.66, 0.56)
    render([(hood, tan)], 25, -60, "drumcase_front.png")
    render([(hood, tan)], 25, 120, "drumcase_back.png")
    render([(hood, tan)], -35, -60, "drumcase_under.png")
    render([(hood, tan), (cover, grey)], 20, -120, "drumcase_assembly.png")
