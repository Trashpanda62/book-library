#!/usr/bin/env python3
"""Generate PWA icons: a little shelf of book spines on sage, matching the app theme."""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SAGE = (91, 114, 99)        # --sage
SAGE_D = (66, 81, 70)       # --sage-dark
CREAM = (245, 241, 232)     # --paper
ACCENT = (184, 104, 63)     # --accent
SAGE_L = (140, 163, 146)    # --sage-light
GOLD = (200, 170, 90)

def rounded(size, radius_frac=0.22, bg=SAGE):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(size * radius_frac)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=bg)
    return img, d

def draw_books(img, d, size, full_bleed=False):
    # a row of book spines, slightly varied, sitting on a shelf line
    inset = size * (0.16 if full_bleed else 0.20)
    shelf_y = size - inset
    top_min = inset + size * 0.06
    spines = [
        (CREAM, 0.055, 0.62),
        (ACCENT, 0.075, 0.74),
        (SAGE_L, 0.055, 0.55),
        (CREAM, 0.070, 0.70),
        (GOLD, 0.055, 0.60),
    ]
    total_w = sum(w for _, w, _ in spines) * size
    gap = size * 0.018
    x = (size - total_w - gap * (len(spines) - 1)) / 2
    for col, w, h in spines:
        bw = w * size
        bh = h * (shelf_y - top_min)
        y0 = shelf_y - bh
        rad = max(2, int(bw * 0.18))
        d.rounded_rectangle([x, y0, x + bw, shelf_y], radius=rad, fill=col)
        # a couple of title bands
        band = tuple(int(c * 0.62) for c in col[:3])
        d.rectangle([x + bw * 0.2, y0 + bh * 0.18, x + bw * 0.8, y0 + bh * 0.24], fill=band)
        d.rectangle([x + bw * 0.2, y0 + bh * 0.30, x + bw * 0.8, y0 + bh * 0.35], fill=band)
        x += bw + gap
    # shelf line
    d.rectangle([inset * 0.7, shelf_y, size - inset * 0.7, shelf_y + size * 0.03], fill=SAGE_D)

def make(size, path, full_bleed=False):
    if full_bleed:
        img = Image.new("RGBA", (size, size), SAGE + (255,))
        d = ImageDraw.Draw(img)
    else:
        img, d = rounded(size)
    draw_books(img, d, size, full_bleed)
    img.save(path)
    print("wrote", path)

# regular rounded icons
big, _ = None, None
img512, d512 = rounded(512); draw_books(img512, d512, 512, False); img512.save(os.path.join(HERE, "icon-512.png")); print("wrote icon-512.png")
img192 = img512.resize((192, 192), Image.LANCZOS); img192.save(os.path.join(HERE, "icon-192.png")); print("wrote icon-192.png")
# maskable (full-bleed, books in safe zone)
make(512, os.path.join(HERE, "icon-maskable-512.png"), full_bleed=True)
# apple touch (full square, no transparency)
appleimg = Image.new("RGB", (512, 512), SAGE)
ad = ImageDraw.Draw(appleimg); draw_books(appleimg, ad, 512, True)
appleimg.resize((180, 180), Image.LANCZOS).save(os.path.join(HERE, "apple-touch-icon.png")); print("wrote apple-touch-icon.png")
# favicon
img512.resize((32, 32), Image.LANCZOS).save(os.path.join(HERE, "favicon.png")); print("wrote favicon.png")
