"""Кадры «работает за столом» сбоку: из готового кадра sitSide убираем руку с коленей
и дорисовываем согнутую руку (плечо → локоть → кисть), которая лежит на столешнице:
рисует стилусом или подносит кружку ко рту.

Кадр привязан к месту: ноги, которые уходят под стол, стираются по контуру стола из фона,
поэтому в игре колени прячутся под столешницу, а рука лежит сверху.

Координаты рук — в пикселях исходного кадра (assets/cut/<slug>_sitSide.png, лицом вправо).
Место и стол — в пикселях фона (studio-bg2.jpg, 2000×1493).
Разметка по людям — в assets/cut/desk_rigs.json (там имена, в git не кладём).
Пишет <slug>_deskSide, <slug>_drawSide1..3, <slug>_sipSide1..3 — atlas.py подхватывает их сам.
"""
import json
import math
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
CUT = os.path.join(HERE, "..", "assets", "cut")
SS = 3                      # рисуем с запасом и уменьшаем — края мягкие, как у основного арта
PAD = 60                    # поля слева и справа, центр кадра (ноги) остаётся на месте
K = .62 * .85               # пиксель кадра → пиксель фона (atlas .62 × scaleOf .85 / 5 × 5)
INK = (8, 6, 20, 255)       # контур
UPPER, FORE = 70, 80        # длина плеча и предплечья, px кадра

RIGS = json.load(open(os.path.join(CUT, "desk_rigs.json"), encoding="utf-8"))


def to_cut(rig, w, h, bx, by):
    """Пиксель фона → пиксель кадра (без полей) с учётом места и разворота."""
    sx, sy = rig["seat"]
    return w / 2 + (bx - sx) / K * rig["face"], h - (sy - by) / K


def elbow_for(sh, hand, down=1):
    """Где локоть, чтобы плечо и предплечье заданной длины дотянулись до кисти (локоть вниз)."""
    dx, dy = hand[0] - sh[0], hand[1] - sh[1]; d = min(math.hypot(dx, dy), UPPER + FORE - 1)
    a = math.acos(max(-1, min(1, (UPPER ** 2 + d ** 2 - FORE ** 2) / (2 * UPPER * d))))
    base = math.atan2(dy, dx) + a * down
    return sh[0] + math.cos(base) * UPPER, sh[1] + math.sin(base) * UPPER


def capsule(d, a, b, r, fill):
    d.line([a, b], fill=fill, width=int(r * 2))
    for p in (a, b): d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)


def body(base, rig, erase=True):
    """Кадр без руки на коленях и без того, что спрятано столом."""
    w, h = base.size
    big = Image.new("RGBA", ((w + PAD * 2) * SS, h * SS), (0, 0, 0, 0))
    big.alpha_composite(base.resize((w * SS, h * SS), Image.NEAREST), (PAD * SS, 0))
    d = ImageDraw.Draw(big)
    S = lambda p: ((p[0] + PAD) * SS, p[1] * SS)
    if erase:
        x0, y0, x1, y1 = rig["erase"]
        # пальто спускается от груди к коленям по диагонали, перед ним — пусто до бедра
        f0, f1 = rig["front"], rig["front_lap"]
        d.rectangle([S((f0, y0)), S((x1, y1))], fill=(0, 0, 0, 0))
        # заливка — плавный переход от пальто слева к пальто снизу, без шва и без «заплатки»
        src = base.load(); m = Image.new("L", big.size, 0)
        ImageDraw.Draw(m).polygon([S((x0, y0)), S((f0, y0)), S((f1, y1)), S((x0, y1))], fill=255)
        fill = Image.new("RGBA", big.size, (0, 0, 0, 0)); fp = ImageDraw.Draw(fill)
        ok = lambda c: c[3] > 200 and max(c[:3]) > 28 and c[0] - c[2] < 30   # без контура и пуговиц
        def avg(pts, dflt):
            cs = [src[p] for p in pts if ok(src[p])]
            return tuple(sum(c[i] for c in cs) / len(cs) for i in range(3)) + (255,) if cs else dflt
        # цвет снизу — среднее по полоске под вырезом (без отдельных столбиков)
        Bs = {u: avg([(min(max(uu, x0), f1 - 6), vv) for uu in range(u - 6, u + 7) for vv in range(y1 + 3, y1 + 8)], None) for u in range(x0, f0 + 1)}
        for v in range(y0, y1 + 1):
            Lc = avg([(uu, vv) for uu in range(x0 - 10, x0 - 3) for vv in range(v - 2, v + 3)], rig["sleeve"])
            for u in range(x0, f0 + 1):
                Bc = Bs[u] or Lc
                tv, tu = (v - y0) / (y1 - y0), (u - x0) / max(1, f0 - x0)
                wB = tv * tv; wL = (1 - tu) * (1 - wB)
                k = wB / (wB + wL + 1e-6)
                c = tuple(round(Lc[i] * (1 - k) + Bc[i] * k) for i in range(3)) + (255,)
                fp.rectangle([S((u, v)), S((u + 1, v + 1))], fill=c)
        big.paste(fill, mask=m)
        d.line([S((f0, y0 - 4)), S((f1, y1))], fill=INK, width=6 * SS)
    # стол: всё, что ниже колен и попадает на стол, — под столом
    m = Image.new("L", big.size, 0)
    ImageDraw.Draw(m).polygon([S(to_cut(rig, w, h, *p)) for p in rig["desk"]], fill=255)
    a = big.getchannel("A"); a.paste(0, mask=m); big.putalpha(a)
    return big, d, S


def arm(d, S, rig, hand, prop):
    sh, t = tuple(rig["shoulder"]), rig["thick"] / 2
    el = elbow_for(sh, hand)
    dx, dy = hand[0] - el[0], hand[1] - el[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L; nx, ny = uy, -ux
    end = (hand[0] - ux * 14, hand[1] - uy * 14)      # кисть торчит из рукава
    # контур обеих частей, потом заливка — один рукав со сгибом
    capsule(d, S(sh), S(el), (t + 4) * SS, INK); capsule(d, S(el), S(end), (t + 4) * SS, INK)
    capsule(d, S(sh), S(el), (t - 2) * SS, rig["sleeve"]); capsule(d, S(el), S(end), (t - 2) * SS, rig["sleeve"])
    # блик по верху предплечья, манжета, пуговицы
    capsule(d, S((el[0] + nx * t * .45 + ux * 8, el[1] + ny * t * .45 + uy * 8)), S((end[0] + nx * t * .45 - ux * 10, end[1] + ny * t * .45 - uy * 10)), 4 * SS, rig["sleeve_hi"])
    cuff = (end[0] - ux * 10, end[1] - uy * 10)
    d.line([S((cuff[0] + nx * t * .9, cuff[1] + ny * t * .9)), S((cuff[0] - nx * t * .9, cuff[1] - ny * t * .9))], fill=INK, width=4 * SS)
    for k in (-22, -34):
        b = (end[0] + ux * k - nx * t * .4, end[1] + uy * k - ny * t * .4)
        d.ellipse([S((b[0] - 4.5, b[1] - 4.5)), S((b[0] + 4.5, b[1] + 4.5))], fill=rig["button"])
    hx, hy = hand
    d.ellipse([S((hx - 14, hy - 13)), S((hx + 14, hy + 13))], fill=rig["skin_ink"])
    d.ellipse([S((hx - 10, hy - 9)), S((hx + 10, hy + 9))], fill=rig["skin"])
    if prop == "stylus":
        d.line([S((hx - 10, hy - 28)), S((hx + 14, hy + 16))], fill=INK, width=8 * SS)
        d.line([S((hx - 9, hy - 26)), S((hx + 11, hy + 11))], fill=(150, 156, 176, 255), width=3 * SS)
        d.ellipse([S((hx - 8, hy - 8)), S((hx + 6, hy + 6))], fill=rig["skin"])
    if prop == "mug":   # кружка перед кистью, пальцы поверх края
        mx, my = hx + 13, hy - 4
        d.rounded_rectangle([S((mx - 17, my - 22)), S((mx + 17, my + 20))], radius=7 * SS, fill=INK)
        d.rounded_rectangle([S((mx - 12, my - 17)), S((mx + 12, my + 15))], radius=5 * SS, fill=(238, 230, 214, 255))
        d.ellipse([S((mx - 12, my - 22)), S((mx + 12, my - 12))], fill=INK)
        d.ellipse([S((mx - 9, my - 19)), S((mx + 9, my - 15))], fill=(110, 64, 36, 255))
        d.rectangle([S((mx - 12, my - 1)), S((mx + 12, my + 5))], fill=(196, 70, 62, 255))
        d.ellipse([S((hx - 12, hy - 8)), S((hx + 1, hy + 8))], fill=rig["skin"])
    return el


def finish(big, w, h):
    out = big.resize((w + PAD * 2, h), Image.LANCZOS)
    out.putalpha(out.getchannel("A").point(lambda v: 255 if v > 120 else 0))
    return out


def main():
    for slug, rig in RIGS.items():
        rig = {k: tuple(v) if isinstance(v, list) and not isinstance(v[0], list) else v for k, v in rig.items()}
        base = Image.open(os.path.join(CUT, f"{slug}_sitSide.png")).convert("RGBA")
        w, h = base.size
        save = lambda img, name: img.save(os.path.join(CUT, f"{slug}_{name}.png"))
        # просто сидит за столом: рука на коленях, ноги под столом
        big, d, S = body(base, rig, erase=False); save(finish(big, w, h), "deskSide")
        # рисует: кисть на бумагах, стилус ходит
        hand = to_cut(rig, w, h, *rig["hand_bg"])
        for i, (ox, oy) in enumerate([(0, 0), (7, -3), (2, 3)], 1):
            big, d, S = body(base, rig); el = arm(d, S, rig, (hand[0] + ox, hand[1] + oy), "stylus"); save(finish(big, w, h), f"drawSide{i}")
        # кофе: кружка на столе → на полпути → у рта
        mouth = (rig["mouth"][0] - 12, rig["mouth"][1] + 24)
        mid = ((hand[0] + mouth[0]) / 2 + 6, (hand[1] + mouth[1]) / 2 - 4)
        for i, pt in enumerate([hand, mid, mouth], 1):
            big, d, S = body(base, rig); arm(d, S, rig, pt, "mug"); save(finish(big, w, h), f"sipSide{i}")
        print(slug, "кисть", [round(v) for v in hand], "локоть", [round(v) for v in el])


if __name__ == "__main__":
    main()
