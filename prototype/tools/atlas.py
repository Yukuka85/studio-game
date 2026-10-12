"""Атлас спрайтов из листов art/new style: персонажи (уже нарезаны в assets/cut) + стулья, кот, самоед, мелочи.

    python3 tools/atlas.py   → assets/atlas.png + assets/atlas.json
Масштаб атласа: 1 пиксель = 0.5 пикселя фона в сетке 2000×1493.
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(os.path.dirname(HERE), "art", "new style")
CUT = os.path.join(HERE, "assets", "cut")
PROPS_SRC = [f for f in os.listdir(ART) if f.startswith("Drawing_office_furniture")][0]

# номера компонент на листе предметов → имя и масштаб
PROPS = {
    0: ("chair_front", .41), 3: ("chair_back", .41), 4: ("chair_side", .41), 1: ("chair_34", .41),
    10: ("chair_jacket", .41), 11: ("chair_back2", .41), 12: ("chair_side2", .41), 13: ("chair_dark34", .41),
    20: ("chair_blanket", .41), 22: ("chair_pillow", .41), 21: ("chair_teal34", .41), 23: ("chair_darkback", .41),
    31: ("chair_front2", .41), 34: ("chair_back3", .41), 35: ("chair_back34", .41),
    5: ("cat_sit", .2), 6: ("cat_sleep", .2), 14: ("cat_walk", .2), 15: ("cat_back", .2), 16: ("cat_curl", .2),
    8: ("dog_sit", .26), 9: ("dog_lie", .26), 7: ("dog_sleep", .26), 17: ("dog_walk", .26), 19: ("dog_stand", .26), 18: ("dog_bow", .26), 24: ("dog_lie2", .26),
    25: ("laptop", .22), 26: ("laptop_closed", .22), 28: ("coffee", .2), 27: ("tumbler", .2), 38: ("mug", .2),
    33: ("books", .22), 36: ("pencils", .2), 37: ("bag", .22), 39: ("papers", .22), 32: ("lamp", .24),
    29: ("backpack", .24), 30: ("backpack2", .24), 43: ("trash", .26), 44: ("headphones", .2), 45: ("stickies", .2), 47: ("donut", .2), 46: ("mouse", .2),
    41: ("plant1", .3), 40: ("plant2", .3), 42: ("plant3", .3),
}

def props():
    src = Image.open(os.path.join(ART, PROPS_SRC)).convert("RGB")
    a = np.asarray(src).astype(int)
    fg = a.min(2) < 225
    fg = ndimage.binary_closing(fg, iterations=3); fg = ndimage.binary_fill_holes(fg); fg = ndimage.binary_opening(fg, iterations=2)
    lab, n = ndimage.label(fg)
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    big = [i + 1 for i, s in enumerate(sizes) if s > 6000]
    objs = ndimage.find_objects(lab)
    out = {}
    for idx, li in enumerate(big):
        if idx not in PROPS: continue
        name, sc = PROPS[idx]
        sl = objs[li - 1]
        m = (lab[sl] == li)
        if name == "cat_curl": m[:, int(m.shape[1] * .8):] = False   # справа прилип чужой кусок
        # мягкая тень под стульями (светло-серая) — убираем
        if name.startswith("chair"):   # тень под колёсиками — только у стульев и только внизу
            rgb = a[sl]
            shadow = (rgb.min(2) > 175) & (np.ptp(rgb, axis=2) < 22)
            shadow[: int(shadow.shape[0] * .8)] = False
            m = m & ~shadow
        ys, xs = np.where(m); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        crop = np.asarray(src)[sl][ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        img = Image.fromarray(np.dstack([crop, (m * 255).astype(np.uint8)]))
        img = img.resize((max(1, round(img.width * sc)), max(1, round(img.height * sc))), Image.LANCZOS)
        out[name] = img
    return out

def chars():
    out = {}
    for f in sorted(os.listdir(CUT)):
        if f.endswith(".png"):
            img = Image.open(os.path.join(CUT, f)).convert("RGBA")
            if f == "vadim_lie.png":   # к лежащему прилип кусок гирлянды справа сверху
                px = img.load(); w, h = img.size
                for yy in range(int(h * .5)):
                    for xx in range(int(w * .78), w): px[xx, yy] = (0, 0, 0, 0)
            out["c_" + f[:-4]] = img.resize((round(img.width * .62), round(img.height * .62)), Image.LANCZOS)
    return out

sprites = {**chars(), **props()}
# упаковка полками
W = 2048; x = y = shelf = 0; pos = {}
for name, img in sorted(sprites.items(), key=lambda kv: -kv[1].height):
    if x + img.width + 2 > W: x = 0; y += shelf + 2; shelf = 0
    pos[name] = [x, y, img.width, img.height]; x += img.width + 2; shelf = max(shelf, img.height)
atlas = Image.new("RGBA", (W, y + shelf), (0, 0, 0, 0))
for name, (px, py, w, h) in pos.items(): atlas.paste(sprites[name], (px, py))
atlas.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(os.path.join(HERE, "assets", "atlas.png"), optimize=True)
json.dump(pos, open(os.path.join(HERE, "assets", "atlas.json"), "w"))
print(len(pos), "спрайтов, атлас", atlas.size, os.path.getsize(os.path.join(HERE, "assets", "atlas.png")) // 1024, "KB")
