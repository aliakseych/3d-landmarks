#!/usr/bin/env python3
"""Composite reconstructed-camera renders over the original photos.

usage: compare.py <rendersDir> <photosDir> <out.jpg>
Takes renders/cam_<stem>_<raw|display>.png (transparent film) and photos/<stem>.jpg
(display-oriented). 'raw' renders are in the landscape sensor frame and get rotated
90deg CW (EXIF Orientation=6, i.e. phone/iPad held in portrait). Each row:
photo | render | photo with the render silhouette outline (red) + 50% blend.
A correct pose/scale shows the outline hugging the statue in every row.
"""
import glob, os, sys
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

rd, pd, out = sys.argv[1:4]
rows = []
for p in sorted(glob.glob(os.path.join(rd, "cam_*.png"))):
    base = os.path.basename(p)[4:-4]
    stem, frame = base.rsplit("_", 1)
    ph = Image.open(os.path.join(pd, stem + ".jpg")).convert("RGB")
    r = Image.open(p).convert("RGBA")
    if frame == "raw":
        r = r.rotate(-90, expand=True)
    r = r.resize(ph.size)
    a = np.asarray(r)[:, :, 3] > 10
    edge = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3))
    blend = Image.blend(ph, Image.alpha_composite(ph.convert("RGBA"), r).convert("RGB"), 0.5)
    blend.paste((255, 0, 0), mask=edge)
    rbg = Image.alpha_composite(Image.new("RGBA", ph.size, (210, 220, 230, 255)), r).convert("RGB")
    row = Image.new("RGB", (ph.width * 3, ph.height + 30), "white")
    for i, im in enumerate((ph, rbg, blend)):
        row.paste(im, (i * ph.width, 30))
    ImageDraw.Draw(row).text((8, 8), f"{stem} ({frame})", fill="black")
    rows.append(row.resize((row.width // 2, row.height // 2)))
if not rows:
    sys.exit("no cam_*.png renders")
sheet = Image.new("RGB", (rows[0].width, sum(r.height for r in rows)), "white")
y = 0
for r in rows:
    sheet.paste(r, (0, y)); y += r.height
sheet.save(out, quality=85)
print(out, sheet.size)
