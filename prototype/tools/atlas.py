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
        if name.startswith("chair"):   # тень под колёсиками: всё светлое в нижней трети (колёса и крестовина тёмные)
            rgb = a[sl]
            shadow = rgb.min(2) > 120
            shadow[: int(shadow.shape[0] * .66)] = False
            m = m & ~shadow
            m = m & ~((rgb.min(2) > 205) & (np.ptp(rgb, axis=2) < 30))   # запертый внутри контура белый фон листа
            m = ndimage.binary_opening(m, iterations=1)
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

MON_SRC = [f for f in os.listdir(ART) if f.startswith("Draw_game_objects")]
MON_COLS = [570, 1485, 2400, 3330, 4260]
MON_ROWS = {"ghost": (110, 745), "slime": (960, 1625), "zombie": (1790, 2620), "tangle": (2750, 3440)}
MON_POSES = {"ghost": ["front", "side", "back", "float", "play"], "slime": ["front", "side", "back", "action", "splat"],
             "zombie": ["front", "side", "back", "walk", "action"], "tangle": ["front", "side", "back", "roll", "action"]}

def monsters():
    """Лист монстриков: 4 строки × 5 кадров на тёмно-синей сетке с подписями."""
    if not MON_SRC: return {}
    src = Image.open(os.path.join(ART, MON_SRC[0])).convert("RGB")
    a = np.asarray(src).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    navy = (b > r + 22) & (b > g + 10) & (a.max(2) < 125)
    out = {}
    for kind, (y0, y1) in MON_ROWS.items():
        for ci, cx in enumerate(MON_COLS):
            x0, x1 = max(400 if ci == 0 else 0, cx - 450), min(src.width, cx + 450)
            fg = ~navy[y0:y1, x0:x1]
            fg = ndimage.binary_opening(fg, iterations=2)
            lab, n = ndimage.label(fg)
            if not n: continue
            sizes = ndimage.sum(fg, lab, range(1, n + 1)); k = int(np.argmax(sizes)) + 1
            keep = lab == k
            near = ndimage.binary_dilation(keep, iterations=25)
            for j in range(1, n + 1):
                if j != k and 80 < sizes[j - 1] < sizes[k - 1] * .3 and (near & (lab == j)).any(): keep |= lab == j
            keep = ndimage.binary_fill_holes(ndimage.binary_closing(keep, iterations=4))
            ys, xs = np.where(keep)
            crop = np.asarray(src)[y0:y1, x0:x1][ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            m = keep[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            img = Image.fromarray(np.dstack([crop, (m * 255).astype(np.uint8)]))
            out[f"m_{kind}_{MON_POSES[kind][ci]}"] = img.resize((round(img.width * .5), round(img.height * .5)), Image.LANCZOS)
    return out

CUT2 = os.path.join(HERE, "assets", "cut2")
# доп. кадры: анимации Вадима (vb_*) и новые кадры монстриков (mo_*), имена → ключи атласа
EXTRA = {
    "c_vadim_walkSide1": "vb_r0c6", "c_vadim_walkSide2": "vb_r0c7", "c_vadim_walkSide3": "vb_r0c8",
    "c_vadim_typeBack1": "vb_r2c5", "c_vadim_typeBack2": "vb_r2c8", "c_vadim_stretchBack": "vb_r3c7",
    "c_vadim_coffeeFront": "vb_r3c0", "c_vadim_coffeeSide": "vb_r3c2", "c_vadim_coffeeBack": "vb_r3c8",
    "c_vadim_thinkBack1": "vb_r5c4", "c_vadim_thinkBack2": "vb_r5c5", "c_vadim_thinkFront1": "vb_r5c0", "c_vadim_thinkFront2": "vb_r5c1",
    "c_vadim_joy1": "vb_r4c1", "c_vadim_joy2": "vb_r4c2", "c_vadim_wave": "vb_r4c0", "c_vadim_idea": "vb_r5c6",
    "c_vadim_laptopFront": "vb_r2c4", "c_vadim_lieSide": "vb_r6c7",
    "m_ghost_idleF": "mo_r0c0", "m_ghost_idleB": "mo_r0c1", "m_ghost_idleS": "mo_r0c2", "m_ghost_walkF": "mo_r0c3", "m_ghost_walkB": "mo_r0c4",
    "m_ghost_walkS": "mo_r0c5", "m_ghost_sitB": "mo_r0c6", "m_ghost_sitS": "mo_r0c7", "m_ghost_sleepy": "mo_r0c8",
    "m_ghost_walkF2": "mo_r1c3", "m_ghost_walkS2": "mo_r1c5", "m_ghost_sad": "mo_r1c8",
    "m_gghost_idleF": "mo_r1c0", "m_gghost_idleB": "mo_r1c1", "m_gghost_idleS": "mo_r1c2",
    "m_cube_idleF": "mo_r2c0", "m_cube_idleB": "mo_r2c1", "m_cube_idleS": "mo_r2c2", "m_cube_walkF": "mo_r2c3", "m_cube_walkB": "mo_r2c4",
    "m_cube_walkS": "mo_r2c5", "m_cube_melt1": "mo_r2c6", "m_cube_melt2": "mo_r2c7", "m_cube_melt3": "mo_r2c8", "m_cube_puddle": "mo_r2c9",
    "m_zombie_walkS2": "mo_r3c5", "m_zombie_walkS3": "mo_r4c5", "m_zombie_dead": "mo_r3c9",
    "m_tangle_r1": "mo_r5c1", "m_tangle_r2": "mo_r5c3", "m_tangle_r3": "mo_r5c5", "m_tangle_r4": "mo_r5c7", "m_tangle_dead": "mo_r5c9",
}

def despeck(img):
    """Синие крошки фона, прилипшие к краю: мелкие синие островки, касающиеся прозрачного. Джинсы (крупные) не трогаем."""
    a = np.asarray(img).astype(int); rgb, al = a[:, :, :3], a[:, :, 3] > 0
    navy = al & (rgb[:, :, 2] > rgb[:, :, 0] + 8) & (rgb[:, :, 2] > 45) & (rgb[:, :, 0] < 110) & (rgb.max(2) < 125)
    lab, n = ndimage.label(navy)
    if not n: return img
    border = ndimage.binary_dilation(~al, iterations=1)
    sizes = ndimage.sum(navy, lab, range(1, n + 1))
    touch = ndimage.maximum(border, lab, range(1, n + 1))
    drop = [i + 1 for i in range(n) if sizes[i] < 4500 and touch[i]]
    out = np.asarray(img).copy(); out[np.isin(lab, drop), 3] = 0
    return Image.fromarray(out)

def extra():
    out = {}
    for key, src in EXTRA.items():
        f = os.path.join(CUT2, src + ".png")
        if not os.path.exists(f): print("нет кадра", src); continue
        img = despeck(Image.open(f).convert("RGBA"))
        k = .62 if key.startswith("c_") else .5
        out[key] = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    return out

sprites = {**chars(), **props(), **monsters(), **extra()}
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
