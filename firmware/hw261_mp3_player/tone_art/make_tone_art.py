"""Drum player menu art with a Tone button and a Bass/Treble popup.

Same style as the coffee player's buttons (make_menu_art3.py), but 29 px tall so
eight rows fit the 272-pixel screen. The new pictures go at ids 33+; the reels
(19-30) are copied from the coffee player. The coffee buttons (0-18, 31-32) are not
used here and become 2x2 black placeholders: the screen silently drops the end of a
9.ICO much over the stock 219 KB (a 250 KB file lost icons from 49 on), so the file
must stay small. This 9.ICO is for the drum player only.

  33-50  normal/highlighted for each menu item, in ITEM order:
         Prev, Next, Random, Play song, Loop, Halloween, Volume, Mono, Tone
  51-53  editing: Play song, Loop one song, Volume
  54-55  Stereo, normal/highlighted
  56-58  popup Bass: normal/highlighted/editing
  59-61  popup Treble: normal/highlighted/editing
  62-63  popup Done: normal/highlighted

Usage: python make_tone_art.py <existing lib9_src folder> <output folder>
Writes <output>/lib9_src/0..63.jpg.
"""
import os
import shutil
import sys
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
lib = os.path.join(out, "lib9_src")
os.makedirs(lib, exist_ok=True)
for n in range(33):
    if 19 <= n <= 30:  # Reels.
        shutil.copy(os.path.join(src, f"{n}.jpg"), os.path.join(lib, f"{n}.jpg"))
    else:  # Unused coffee button: keep the id, drop the picture.
        Image.new("RGB", (2, 2)).save(os.path.join(lib, f"{n}.jpg"), quality=90, progressive=False)

FULL, HALF, H = 182, 88, 29
font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 16)
WHITE = (255, 255, 255)
STYLES = {
    "normal": ((76, 88, 108), ((128, 140, 162), (102, 114, 136)), ((26, 32, 44), (44, 52, 66)), False),
    "hi": ((204, 85, 0), ((246, 150, 80), (226, 118, 40)), ((110, 42, 0), (150, 60, 0)), False),
    "edit": ((178, 70, 0), ((246, 150, 80), (226, 118, 40)), ((100, 38, 0), (140, 56, 0)), True),
}


def button(label, w, state):
    color, light, dark, sunken = STYLES[state]
    img = Image.new("RGB", (w, H), color)
    d = ImageDraw.Draw(img)
    if sunken:
        light, dark = dark, light
    for i in range(2):
        d.line([(i, i), (w - 1 - i, i)], fill=light[i])
        d.line([(i, i), (i, H - 1 - i)], fill=light[i])
        d.line([(i, H - 1 - i), (w - 1 - i, H - 1 - i)], fill=dark[i])
        d.line([(w - 1 - i, i), (w - 1 - i, H - 1 - i)], fill=dark[i])
    x = w // 2 if w == HALF else 12
    y = H // 2 + (1 if state == "edit" else 0)
    anchor = "mm" if w == HALF else "lm"
    d.text((x + 1, y + 1), label, font=font, fill=(30, 20, 15), anchor=anchor)  # Shadow.
    d.text((x, y), label, font=font, fill=WHITE, anchor=anchor)
    return img


ITEMS = [("<< Prev", HALF), ("Next >>", HALF), ("Play Random", FULL), ("Play song", FULL),
         ("Loop one song", FULL), ("Play Halloween", FULL), ("Volume", FULL), ("Mono", FULL),
         ("Tone", FULL)]
icons = []
for label, w in ITEMS:
    icons += [button(label, w, "normal"), button(label, w, "hi")]
icons += [button(label, FULL, "edit") for label in ("Play song", "Loop one song", "Volume")]
icons += [button("Stereo", FULL, "normal"), button("Stereo", FULL, "hi")]
for label in ("Bass", "Treble"):
    icons += [button(label, FULL, s) for s in ("normal", "hi", "edit")]
icons += [button("Done", FULL, "normal"), button("Done", FULL, "hi")]

for n, img in enumerate(icons, start=33):
    assert img.width % 2 == 0  # The display garbles odd widths.
    img.save(os.path.join(lib, f"{n}.jpg"), quality=90, progressive=False, subsampling=0)
print(len(icons), "new icons, ids 33 -", 32 + len(icons))
