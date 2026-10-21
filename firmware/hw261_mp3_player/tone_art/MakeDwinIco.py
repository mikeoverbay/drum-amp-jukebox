"""Pack numbered JPGs (0.jpg, 1.jpg, ...) into a DWIN T5UIC1 icon library (.ICO).

Layout (matches the stock Ender-3 V2 9.ICO): a 4096-byte table of 256 entries,
16 bytes each, all big-endian:
  width (2), height (2), offset from file start (4), length (3), zero (5)
then the JPG data back to back from offset 0x1000. Unused entries are all zero.

Usage: python MakeDwinIco.py <folder with N.jpg> <output .ICO>
"""
import os
import struct
import sys

from PIL import Image

src, out = sys.argv[1], sys.argv[2]
jpgs = []
for n in range(256):
    path = os.path.join(src, f"{n}.jpg")
    if not os.path.exists(path):
        break
    with Image.open(path) as im:
        if im.format != "JPEG" or im.info.get("progressive"):
            sys.exit(f"{path}: must be a baseline JPG")
        size = im.size
    data = open(path, "rb").read()
    if len(data) > 32 * 1024:
        sys.exit(f"{path}: {len(data)} bytes, over the 32 KB limit")
    jpgs.append((size, data))
if not jpgs:
    sys.exit("no 0.jpg found")

table = bytearray(4096)
blob = bytearray()
for n, ((w, h), data) in enumerate(jpgs):
    offset = 4096 + len(blob)
    struct.pack_into(">HHI", table, n * 16, w, h, offset)
    table[n * 16 + 8:n * 16 + 11] = len(data).to_bytes(3, "big")
    blob += data
with open(out, "wb") as f:
    f.write(table + blob)
print(f"{out}: {len(jpgs)} icons, {4096 + len(blob)} bytes")
