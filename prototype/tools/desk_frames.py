"""Кадры «работает за столом»: руки тянутся к предметам на своём столе.

Боком (sitSide): убираем руку с коленей, рисуем ближнюю руку поверх тела.
Спиной (sitBack): спинка кресла закрывает всё ниже головы, руки идут за головой к столу
или поднимаются вверх; висящие руки стираем.

Рука = плечо + предплечье (локоть считается сам), текстура рукава и кисть берутся из бокового
кадра этого же человека — клетка, пуговицы, манжеты остаются свои.
Боковой кадр привязан к месту: то, что ниже колен и попадает на стол, стирается по контуру стола.

Координаты: цели — в пикселях фона (studio-bg2.jpg) или относительно тела («@mouth» и т.п.);
всё остальное — в пикселях исходных кадров assets/cut/<slug>_<поза>.png (лицом вправо).
Разметка — assets/cut/desk_rigs.json (там имена, в git не кладём).
Пишет <slug>_desk (сидит, ноги под столом) и <slug>_d_<действие><n>.png — atlas.py подхватывает сам.
"""
import json
import math
import os
import sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
CUT = os.path.join(HERE, "..", "assets", "cut")
SS = 3                      # рисуем с запасом и уменьшаем — края мягкие, как у основного арта
PAD = 110                   # поля по бокам: руки уходят за край кадра, центр (место) не сдвигается
K = .62 * .85               # пиксель кадра → пиксель фона
INK = (8, 6, 20, 255)


def load(name):
    return Image.open(os.path.join(CUT, name + ".png")).convert("RGBA")


def tup(v):
    return tuple(v) if isinstance(v, list) else v


class Rig:
    def __init__(self, slug, r):
        self.slug, self.r = slug, r
        self.kind = r["kind"]
        self.base = load(f"{slug}_{r.get('base') or {'side': 'sitSide', 'back': 'sitBack', 'bstand': 'back', 'front': 'stand'}[self.kind]}")
        self.w, self.h = self.base.size
        side = load(f"{slug}_sitSide")
        box = lambda k: side.crop(tuple(r["tex"][k])) if k in r["tex"] else None
        self.fore, self.upper, self.hand = box("fore"), box("upper") or box("fore"), box("hand")
        self.upper_len, self.fore_len = r.get("upper_len", 70), r.get("fore_len", 82)
        self.mug = mug_image(r["mug_src"]) if r.get("mug_src") else None

    def mug_dir(self, side):
        return -1 if side == "L" else 1          # левой рукой кружку держат слева от кисти

    def mug_hand(self, side="near"):
        """Где кисть, чтобы кружка в руке стояла ровно на своём месте на столе."""
        bx, by = self.r["mug_at"]; u, v = self.to_cut(bx, by)
        mw, mh = self.mug.size
        return u - (mw / 2 - 6) * self.mug_dir(side), v - mh / 2 + 4

    def to_cut(self, bx, by):
        sx, sy = self.r["seat"]
        return self.w / 2 + (bx - sx) / K * self.r["face"], self.h - (sy - by) / K

    def target(self, t):
        if isinstance(t, str):            # «@mouth+dx,dy» — точка тела в пикселях кадра
            name, _, off = t[1:].partition("+")
            p = self.r["body"][name]; dx, dy = map(float, off.split(",")) if off else (0, 0)
            return p[0] + dx, p[1] + dy
        return self.to_cut(*t) if "seat" in self.r else tuple(t)     # без места — точки прямо в пикселях кадра

    def S(self, p):
        return ((p[0] + PAD) * SS, p[1] * SS)

    def canvas(self):
        return Image.new("RGBA", ((self.w + PAD * 2) * SS, self.h * SS), (0, 0, 0, 0))

    def base_big(self):
        big = self.canvas()
        big.alpha_composite(self.base.resize((self.w * SS, self.h * SS), Image.NEAREST), (PAD * SS, 0))
        return big


def mug_image(key):
    """Кружка из листа предметов (атлас): в игре она стоит на столе спрайтом key, в руке — она же."""
    at = Image.open(os.path.join(HERE, "..", "assets", "atlas.png")).convert("RGBA")
    f = json.load(open(os.path.join(HERE, "..", "assets", "atlas.json")))[key]
    img = at.crop((f[0], f[1], f[0] + f[2], f[1] + f[3]))
    k = .5 / K                                   # предметы рисуются в масштабе .5 от атласа
    return img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)


def capsule(d, a, b, r, fill):
    d.line([a, b], fill=fill, width=max(1, int(r * 2)))
    for p in (a, b): d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)


def seg(rig, img, p, q, tex):
    """Кусок руки от p до q: текстура рукава вдоль отрезка, концы скруглены, по краю — контур."""
    T = tex.height; L = math.hypot(q[0] - p[0], q[1] - p[1]); ang = math.atan2(q[1] - p[1], q[0] - p[0])
    d = ImageDraw.Draw(img)
    capsule(d, rig.S(p), rig.S(q), (T / 2 + 1) * SS, INK)
    t = tex.resize((max(2, int((L + T) * SS)), T * SS), Image.LANCZOS).rotate(-math.degrees(ang), resample=Image.BICUBIC, expand=True)
    mx, my = rig.S(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); layer.paste(t, (int(mx - t.width / 2), int(my - t.height / 2)))
    m = Image.new("L", img.size, 0); capsule(ImageDraw.Draw(m), rig.S(p), rig.S(q), (T / 2 - 5) * SS, 255)
    a = Image.composite(layer.getchannel("A"), Image.new("L", img.size, 0), m); layer.putalpha(a)
    img.alpha_composite(layer)


def elbow_for(sh, hand, l1, l2, side):
    dx, dy = hand[0] - sh[0], hand[1] - sh[1]; d = max(1e-3, min(math.hypot(dx, dy), l1 + l2 - 1))
    a = math.acos(max(-1, min(1, (l1 ** 2 + d ** 2 - l2 ** 2) / (2 * l1 * d))))
    base = math.atan2(dy, dx) + a * side
    return sh[0] + math.cos(base) * l1, sh[1] + math.sin(base) * l1


def prop(rig, img, hand, kind, ang, mdir=1):
    d = ImageDraw.Draw(img); S = rig.S; hx, hy = hand
    if kind == "phone":
        d.rounded_rectangle([S((hx - 9, hy - 30)), S((hx + 9, hy + 2))], radius=4 * SS, fill=INK)
        d.rounded_rectangle([S((hx - 6, hy - 27)), S((hx + 6, hy - 1))], radius=2 * SS, fill=(120, 200, 255, 255))
        d.ellipse([S((hx - 11, hy - 8)), S((hx + 3, hy + 6))], fill=tuple(rig.r.get("skin", [240, 180, 150])) + (255,))
        return
    if kind == "marker":
        d.line([S((hx - 2, hy - 30)), S((hx + 4, hy + 6))], fill=INK, width=9 * SS)
        d.line([S((hx - 1, hy - 28)), S((hx + 3, hy + 2))], fill=(226, 64, 70, 255), width=4 * SS)
        return
    if kind in ("stylus", "pen"):
        col = (150, 156, 176, 255) if kind == "stylus" else (60, 110, 200, 255)
        d.line([S((hx - 10, hy - 28)), S((hx + 14, hy + 16))], fill=INK, width=8 * SS)
        d.line([S((hx - 9, hy - 26)), S((hx + 11, hy + 11))], fill=col, width=3 * SS)
    if kind == "mug" and rig.mug:
        m = rig.mug.resize((rig.mug.width * SS, rig.mug.height * SS), Image.LANCZOS)
        if rig.r.get("face", 1) < 0: m = m.transpose(Image.FLIP_LEFT_RIGHT)   # кадр потом отразят — кружка выйдет как на столе
        cx, cy = S((hx + (rig.mug.width / 2 - 6) * mdir, hy - 4)); img.alpha_composite(m, (int(cx - m.width / 2), int(cy - m.height / 2)))
        f = (hx - 9, hy - 6, hx + 1, hy + 6) if mdir > 0 else (hx - 1, hy - 6, hx + 9, hy + 6)      # пальцы поверх края кружки
        d.ellipse([S(f[:2]), S(f[2:])], fill=tuple(rig.r.get("skin", [240, 180, 150])) + (255,))
        return
    if kind == "mug":
        c = rig.r.get("mug", {"body": [238, 230, 214], "band": [196, 70, 62]})
        mx, my = hx + 13, hy - 4
        d.rounded_rectangle([S((mx - 17, my - 22)), S((mx + 17, my + 20))], radius=7 * SS, fill=INK)
        d.rounded_rectangle([S((mx - 12, my - 17)), S((mx + 12, my + 15))], radius=5 * SS, fill=tuple(c["body"]) + (255,))
        d.ellipse([S((mx - 12, my - 22)), S((mx + 12, my - 12))], fill=INK)
        d.ellipse([S((mx - 9, my - 19)), S((mx + 9, my - 15))], fill=(110, 64, 36, 255))
        d.rectangle([S((mx - 12, my - 1)), S((mx + 12, my + 5))], fill=tuple(c["band"]) + (255,))


# ---------- рука v2: в стиле основного арта ----------
# Одна сплошная форма (плечо шире, к запястью уже) без стыков, объём в три тона, контур — тёмный оттенок
# своей же ткани (у кожи — бордовый), крупный кулачок шире запястья, и всё разбито на «пиксели» арта (~5 px).
STYLE = int(os.environ.get("ARM_STYLE", "2"))
PIX = 5

def tone(c, k):
    return tuple(max(0, min(255, round(v * k))) for v in c[:3]) + (255,)


def palette(rig):
    if hasattr(rig, "_pal"): return rig._pal
    import numpy as np
    a = np.asarray(rig.fore.convert("RGBA")).reshape(-1, 4).astype(int)
    m = (a[:, 3] > 200) & (a[:, :3].max(1) > 45)
    base = tuple(int(v) for v in np.median(a[m][:, :3], 0)) if m.any() else (90, 90, 100)
    if rig.r.get("sleeve_rgb"): base = tuple(rig.r["sleeve_rgb"])
    skin = tuple(rig.r.get("skin", [240, 186, 156]))
    ink = tuple(rig.r.get("skin_ink", [120, 46, 40]))
    rig._pal = {
        "cloth": (tone(base, .74), tone(base, 1), tone(base, 1.2), tuple(min(255, max(0, round(v))) for v in (base[0] * .38 + 10, base[1] * .36, base[2] * .4 + 6)) + (255,)),
        "skin": (tone(skin, .84), tone(skin, 1), tone(skin, 1.08), tuple(ink) + (255,)),
    }
    return rig._pal


def arm(rig, img, spec):
    """spec: {"from": "near"|"L"|"R", "to": цель, "prop": ..., "bend": ±1}"""
    if STYLE >= 2: return arm2(rig, img, spec)
    side = spec.get("from", "near")
    sh = tup(rig.r["shoulders"][side])
    if spec["to"] == "mug": hand = rig.mug_hand(side)
    elif spec["to"] == "@sipmid": hand = ((rig.mug_hand(side)[0] + rig.target("@mouth")[0]) / 2 + 8, (rig.mug_hand(side)[1] + rig.target("@mouth")[1]) / 2)
    else: hand = rig.target(spec["to"])
    el = elbow_for(sh, hand, rig.upper_len, rig.fore_len, spec.get("bend", -1 if side == "L" else 1))
    reach = math.hypot(hand[0] - sh[0], hand[1] - sh[1])
    if reach > rig.upper_len + rig.fore_len: print(f"  ! {rig.slug}: не дотягивается до {spec['to']} ({reach:.0f} > {rig.upper_len + rig.fore_len})")
    ang = math.atan2(hand[1] - el[1], hand[0] - el[0])
    hw = rig.hand.width * .45
    cuff = (hand[0] - math.cos(ang) * hw, hand[1] - math.sin(ang) * hw)
    seg(rig, img, sh, el, rig.upper)
    seg(rig, img, el, cuff, rig.fore)
    if rig.r.get("buttons"):
        ux, uy = math.cos(ang), math.sin(ang); nx, ny = uy, -ux; t = rig.fore.height / 2; d = ImageDraw.Draw(img)
        for k in (-16, -28):
            b = (cuff[0] + ux * k - nx * t * .35, cuff[1] + uy * k - ny * t * .35)
            d.ellipse([rig.S((b[0] - 4.5, b[1] - 4.5)), rig.S((b[0] + 4.5, b[1] + 4.5))], fill=tuple(rig.r["buttons"]) + (255,))
    hd = rig.hand.resize((rig.hand.width * SS, rig.hand.height * SS), Image.LANCZOS).rotate(-math.degrees(ang), resample=Image.BICUBIC, expand=True)
    hx, hy = rig.S(hand); img.alpha_composite(hd, (int(hx - hd.width / 2), int(hy - hd.height / 2)))
    if spec.get("prop"): prop(rig, img, hand, spec["prop"], ang, spec.get("mdir", rig.mug_dir(side)))
    return el


def arm2(rig, img, spec):
    side = spec.get("from", "near")
    sh = tup(rig.r["shoulders"][side])
    if spec["to"] == "mug": hand = rig.mug_hand(side)
    elif spec["to"] == "@sipmid": hand = ((rig.mug_hand(side)[0] + rig.target("@mouth")[0]) / 2 + 8, (rig.mug_hand(side)[1] + rig.target("@mouth")[1]) / 2)
    else: hand = rig.target(spec["to"])
    l1, l2 = rig.upper_len, rig.fore_len
    el = elbow_for(sh, hand, l1, l2, spec.get("bend", -1 if side == "L" else 1))
    # недотягивается — рука вытянута в сторону цели, кисть на конце (не растягиваем)
    d = math.hypot(hand[0] - el[0], hand[1] - el[1])
    if d > l2: hand = (el[0] + (hand[0] - el[0]) / d * l2, el[1] + (hand[1] - el[1]) / d * l2)
    ang = math.atan2(hand[1] - el[1], hand[0] - el[0]); ux, uy = math.cos(ang), math.sin(ang)
    T = rig.r.get("arm_w", min(46, rig.fore.height))          # толщина у плеча, px кадра
    r_sh, r_el, r_wr = T * .5, T * .44, T * .36
    hr = T * .43                                              # кулачок
    wrist = (hand[0] - ux * hr * .55, hand[1] - uy * hr * .55)
    pal = palette(rig); cloth, skin = pal["cloth"], pal["skin"]
    short = rig.r.get("short_sleeve")                         # доля длины от плеча, где кончается рукав
    # точки вдоль руки с радиусами
    pts = []
    for (a, b, ra, rb) in ((sh, el, r_sh, r_el), (el, wrist, r_el, r_wr)):
        L = max(1, math.hypot(b[0] - a[0], b[1] - a[1])); n = max(2, int(L / 2))
        for i in range(n + 1):
            t = i / n; pts.append(((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), ra + (rb - ra) * t))
    total = len(pts)
    W, H = img.size
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay); S = rig.S
    def disc(p, r, c): x, y = S(p); dl.ellipse([x - r * SS, y - r * SS, x + r * SS, y + r * SS], fill=c)
    OUT = 5
    # контур: у бокового вида плечо уходит в тело без обводки (рукав той же ткани)
    no_ol = int(total * .12) if rig.kind == "side" else 0
    for i, (p, r) in enumerate(pts):
        pal_i = skin if short and i / total > short else cloth
        if i >= no_ol: disc(p, r + OUT, pal_i[3])
    def ncol(i): return skin if short and i / total > short else cloth
    for i, (p, r) in enumerate(pts): disc(p, r, ncol(i)[0])                      # тень
    for i, (p, r) in enumerate(pts):                                              # основной тон, сдвинут к свету (вверх)
        disc((p[0], p[1] - r * .16), r * .84, ncol(i)[1])
    for i, (p, r) in enumerate(pts):                                              # тонкий блик по верху
        if 2 < i < total - 3: disc((p[0], p[1] - r * .55), r * .2, ncol(i)[2])
    if short:                                                                     # край короткого рукава
        k = int(total * short); p, r = pts[k]
        disc(p, r + 2, cloth[3]); disc(p, r * .9, cloth[1])
    elif rig.r.get("cuff", True):                                                 # манжета у запястья
        p, r = pts[-3]; disc(p, r + 1, cloth[3]); disc(p, r * .92, cloth[0])
    if rig.r.get("stripes"):                                                       # клетка: поперечные полоски
        for j, c in enumerate(rig.r["stripes"]):
            for i in range(4 + j * 7, total - 4, 13):
                p, r = pts[i]
                dl.line([S((p[0] - uy * r * .8, p[1] + ux * r * .8)), S((p[0] + uy * r * .8, p[1] - ux * r * .8))], fill=tuple(c) + (255,), width=3 * SS)
    if rig.r.get("buttons"):
        for k in (-14, -24):
            b = (wrist[0] + ux * k + uy * r_wr * .3, wrist[1] + uy * k - ux * r_wr * .3)
            disc(b, 4, tuple(rig.r["buttons"]) + (255,))
    # кулачок: шире запястья, вытянут вдоль руки; большой палец — тёмная чёрточка
    hx, hy = hand
    hand_lay = Image.new("RGBA", (int(hr * 4 * SS), int(hr * 4 * SS)), (0, 0, 0, 0)); dh = ImageDraw.Draw(hand_lay)
    c0 = hand_lay.width / 2
    def ell(rx, ry, c, ox=0, oy=0): dh.ellipse([c0 + (ox - rx) * SS, c0 + (oy - ry) * SS, c0 + (ox + rx) * SS, c0 + (oy + ry) * SS], fill=c)
    ell(hr * 1.08 + OUT, hr + OUT, skin[3]); ell(hr * 1.08, hr, skin[0]); ell(hr * .95, hr * .82, skin[1], 0, -hr * .14); ell(hr * .35, hr * .25, skin[2], -hr * .2, -hr * .45)
    dh.line([c0 + (hr * .1) * SS, c0 - hr * .55 * SS, c0 + hr * .55 * SS, c0 - hr * .05 * SS], fill=skin[3], width=3 * SS)
    hand_lay = hand_lay.rotate(-math.degrees(ang), resample=Image.BICUBIC)
    hx2, hy2 = S(hand); lay.alpha_composite(hand_lay, (int(hx2 - hand_lay.width / 2), int(hy2 - hand_lay.height / 2)))
    # «пиксели» арта: уменьшаем слой руки до сетки и обратно без сглаживания
    k = SS * PIX
    small = lay.resize((max(1, W // k), max(1, H // k)), Image.BOX)
    small.putalpha(small.getchannel("A").point(lambda v: 255 if v > 110 else 0))
    lay = small.resize((small.width * k, small.height * k), Image.NEAREST)
    img.alpha_composite(lay)
    if spec.get("prop"): prop(rig, img, hand, spec["prop"], ang, spec.get("mdir", rig.mug_dir(side)))
    return el


def body(rig, erase):
    """Тело без лишнего: боком — без руки на коленях; спиной — без висящих рук."""
    big = rig.base_big(); d = ImageDraw.Draw(big); S = rig.S; r = rig.r
    if rig.kind == "side" and erase:
        # туловище под рукой: край — по строкам над рукой и под ней, цвет — плавная «заплатка» (диффузия от краёв)
        import numpy as np
        x0, y0, x1, y1 = r["erase"]
        A = np.asarray(rig.base).astype(float); W, H = rig.w, rig.h
        solid = (A[:, :, 3] > 200) & (A[:, :, :3].max(2) >= 34)
        def front(v):
            us = [u for u in range(x0, min(x1 + 30, W)) if solid[v, u]]
            run = x0
            for u in us:
                if u - run > 3: break
                run = u
            return run
        ft, fb = front(y0 - 6), front(y1 + 6)
        if "front" in r: ft = r["front"]
        if "front_lap" in r: fb = r["front_lap"]
        fr = {v: round(ft + (fb - ft) * (v - y0) / (y1 - y0)) for v in range(y0, y1 + 1)}
        hole = np.zeros((H, W), bool)
        for v in range(y0, y1 + 1): hole[v, x0:fr[v] - 3] = True
        known = solid & ~hole
        if "coat" in r:                                 # опираемся только на ткань туловища, не на бороду и волосы
            known &= np.abs(A[:, :, :3] - np.array(r["coat"], float)).max(2) < r.get("coat_tol", 40)
        img = A[:, :, :3].copy(); img[hole] = A[known][:, :3].mean(0)
        ys, xs = np.where(hole)
        for _ in range(400):
            acc = np.zeros((len(ys), 3)); cnt = np.zeros(len(ys))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = np.clip(ys + dy, 0, H - 1), np.clip(xs + dx, 0, W - 1)
                ok = known[yy, xx] | hole[yy, xx]
                acc[ok] += img[yy[ok], xx[ok]]; cnt[ok] += 1
            img[ys, xs] = acc / np.maximum(cnt, 1)[:, None]
        if r.get("fill") == "mirror":                   # узор (клетка): отражаем ткань сверху и снизу, швы сглажены диффузией
            mid = (y0 + y1) / 2
            for y, x in zip(ys, xs):
                sy = int(y0 - 1 - (y - y0)) if y < mid else int(y1 + 1 + (y1 - y))
                if 0 <= sy < H and solid[sy, x]:
                    k = min(1, abs(y - mid) / 4)          # у середины — мягко в сглаженное
                    img[y, x] = A[sy, x, :3] * k + img[y, x] * (1 - k)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); lp = layer.load()
        for y, x in zip(ys, xs): lp[int(x), int(y)] = tuple(int(c) for c in img[y, x]) + (255,)
        for v in range(y0, y1 + 1):
            for u in range(max(x0, fr[v] - 3), fr[v] + 1): lp[u, v] = INK
        d.rectangle([S((x0, y0)), S((x1, y1))], fill=(0, 0, 0, 0))
        big.alpha_composite(layer.resize((W * SS, H * SS), Image.NEAREST), (PAD * SS, 0))
    if rig.kind in ("back", "bstand", "front"):
        src = rig.base.load()
        for k in erase or []:
            x0, y0, x1, y1 = r["arms"][k]
            d.rectangle([S((x0, y0)), S((x1, y1))], fill=(0, 0, 0, 0))
            if rig.kind == "back": continue
            # у стоящих руки висят вдоль туловища — после них у туловища нет контура: дорисовываем
            inner = x1 + 1 if k == "L" else x0 - 1
            for v in range(y0, y1 + 1):
                if 0 <= inner < rig.w and src[inner, v][3] > 200:
                    a0, a1 = (x1 - 3, x1 + 1) if k == "L" else (x0, x0 + 4)
                    d.rectangle([S((a0, v)), S((a1, v + 1))], fill=INK)
    if rig.kind == "side" and "desk" in r:   # ноги под столом
        m = Image.new("L", big.size, 0)
        ImageDraw.Draw(m).polygon([S(rig.to_cut(*p)) for p in r["desk"]], fill=255)
        a = big.getchannel("A"); a.paste(0, mask=m); big.putalpha(a)
    return big


def finish(rig, big):
    out = big.resize((rig.w + PAD * 2, rig.h), Image.LANCZOS)
    out.putalpha(out.getchannel("A").point(lambda v: 255 if v > 120 else 0))
    return out


def laptop_on_lap(rig, img):
    """Ноутбук на коленях: спрайт из листа предметов, низом на колени (кадр лицом вправо — экран к лицу)."""
    at = Image.open(os.path.join(HERE, "..", "assets", "atlas.png")).convert("RGBA")
    f = json.load(open(os.path.join(HERE, "..", "assets", "atlas.json")))["laptop"]
    lp = at.crop((f[0], f[1], f[0] + f[2], f[1] + f[3])); k = .5 / K
    lp = lp.resize((round(lp.width * k * SS), round(lp.height * k * SS)), Image.LANCZOS).transpose(Image.FLIP_LEFT_RIGHT)
    x, y = rig.S(rig.r["laptop_at"]); img.alpha_composite(lp, (int(x - lp.width / 2), int(y - lp.height)))


def frame(rig, arms, act=None):
    if rig.kind == "side":
        img = body(rig, erase=bool(arms))
        if act == "laptop" and rig.r.get("laptop_at"): laptop_on_lap(rig, img)
        for s in arms: arm(rig, img, s)
        return finish(rig, img)
    img = rig.canvas()                    # спиной: руки позади головы — сначала руки, потом тело; лицом — наоборот
    over = lambda s: s.get("over") or (rig.kind == "front" and (STYLE < 2 or s.get("prop") in ("mug", "phone")))
    for s in arms:
        if not over(s): arm(rig, img, s)
    img.alpha_composite(body(rig, erase=[s.get("from") for s in arms]))
    for s in arms:
        if over(s): arm(rig, img, s)
    return finish(rig, img)


def main(only=None):
    rigs = json.load(open(os.path.join(CUT, "desk_rigs.json"), encoding="utf-8"))
    for slug, r in rigs.items():
        if only and slug not in only: continue
        rig = Rig(slug, r)
        frame(rig, []).save(os.path.join(CUT, f"{slug}_desk.png"))
        n = 0
        for act, frames in r["acts"].items():
            for i, arms in enumerate(frames, 1):
                frame(rig, arms).save(os.path.join(CUT, f"{slug}_d_{act}{i}.png")); n += 1
        print(slug, n, "кадров за столом")
    # занятия там, куда человека бросили: кофе, доска, диван, просто посреди комнаты (pose_rigs.json)
    pp = os.path.join(CUT, "pose_rigs.json")
    if not os.path.exists(pp): return
    for slug, sets in json.load(open(pp, encoding="utf-8")).items():
        if only and slug not in only: continue
        n = 0
        for set_name, r in sets.items():
            rig = Rig(slug, r)
            for act, frames in r["acts"].items():
                for i, arms in enumerate(frames, 1):
                    frame(rig, arms, act).save(os.path.join(CUT, f"{slug}_x_{act}{i}.png")); n += 1
        print(slug, n, "кадров занятий")


if __name__ == "__main__":
    main(sys.argv[1:])
