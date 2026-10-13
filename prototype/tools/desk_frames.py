"""Кадры «работает за столом» сбоку: из готового кадра sitSide убираем руку на коленях
и дорисовываем руку, которая тянется на столешницу — со стилусом и планшетом или с кружкой.

Координаты — в пикселях исходного кадра (assets/cut/<slug>_sitSide.png, лицом вправо).
Для каждого человека в RIGS задано, где у него локоть, предплечье и кисть; цвета берутся из кадра.
Пишет assets/cut/<slug>_drawSide1..3.png и <slug>_sipSide1..3.png — atlas.py подхватывает их сам.
"""
import json
import os
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
CUT = os.path.join(HERE, "..", "assets", "cut")
SS = 3                      # рисуем с запасом и уменьшаем — края мягкие, как у основного арта
PAD = 60                    # поля слева и справа: рука уходит за край кадра, а центр (ноги) остаётся на месте
INK = (8, 6, 20, 255)       # контур

# Разметка по людям (где локоть, края пальто, цвета) — в assets/cut/desk_rigs.json: там имена, в git не кладём
RIGS = json.load(open(os.path.join(CUT, "desk_rigs.json"), encoding="utf-8"))


def capsule(d, a, b, r, fill):
    d.line([a, b], fill=fill, width=int(r * 2))
    for p in (a, b): d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)


def frame(base, rig, hand, prop, prop_at=None, lift=0.0):
    """hand — где кисть; prop: 'stylus' | 'mug'; prop_at — где стоит планшет/кружка."""
    w, h = base.size
    big = Image.new("RGBA", ((w + PAD * 2) * SS, h * SS), (0, 0, 0, 0))
    big.alpha_composite(base.resize((w * SS, h * SS), Image.NEAREST), (PAD * SS, 0))
    d = ImageDraw.Draw(big)
    S = lambda p: ((p[0] + PAD) * SS, p[1] * SS)
    # 1. убрать старую руку: до края пальто — пальто, дальше — пусто; по низу — контур бедра
    x0, y0, x1, y1 = rig["erase"]
    d.rectangle([S((x0, y0)), S((rig["front"], y1))], fill=rig["sleeve"])
    d.rectangle([S((rig["front"], y0)), S((x1, y1))], fill=(0, 0, 0, 0))
    d.line([S((rig["front"], y0 - 2)), S((rig["front"], rig["lap"]))], fill=INK, width=6 * SS)
    # 3. предплечье от локтя к кисти: контур, рукав, блик сверху, пуговицы у манжеты
    e, t = rig["elbow"], rig["thick"] / 2
    dx, dy = hand[0] - e[0], hand[1] - e[1]; L = (dx * dx + dy * dy) ** .5; nx, ny = dy / L, -dx / L
    end = (hand[0] - dx / L * 16, hand[1] - dy / L * 16)     # кисть торчит из рукава
    capsule(d, S(e), S(end), (t + 5) * SS, INK)
    capsule(d, S(e), S(end), (t - 1) * SS, rig["sleeve"])
    hi_a = (e[0] + nx * t * .45, e[1] + ny * t * .45); hi_b = (hand[0] - dx / L * 18 + nx * t * .45, hand[1] - dy / L * 18 + ny * t * .45)
    capsule(d, S(hi_a), S(hi_b), 6 * SS, rig["sleeve_hi"])
    cuff = (hand[0] - dx / L * 30, hand[1] - dy / L * 30)
    d.line([S((cuff[0] + nx * t, cuff[1] + ny * t)), S((cuff[0] - nx * t, cuff[1] - ny * t))], fill=INK, width=5 * SS)
    for k in (-46, -60):
        b = (hand[0] + dx / L * k - nx * t * .45, hand[1] + dy / L * k - ny * t * .45)
        d.ellipse([S((b[0] - 5, b[1] - 5)), S((b[0] + 5, b[1] + 5))], fill=rig["button"])
    # 4. кисть и то, что в ней
    hx, hy = hand
    d.ellipse([S((hx - 15, hy - 15)), S((hx + 15, hy + 15))], fill=rig["skin_ink"])
    d.ellipse([S((hx - 11, hy - 11)), S((hx + 11, hy + 11))], fill=rig["skin"])
    if prop == "mug":   # кружка перед кистью: держит за бок
        mx, my = hx + 14, hy - 4
        d.rounded_rectangle([S((mx - 19, my - 24)), S((mx + 19, my + 22))], radius=7 * SS, fill=INK)
        d.rounded_rectangle([S((mx - 14, my - 19)), S((mx + 14, my + 17))], radius=5 * SS, fill=(238, 230, 214, 255))
        d.ellipse([S((mx - 14, my - 24)), S((mx + 14, my - 13))], fill=INK)
        d.ellipse([S((mx - 10, my - 21)), S((mx + 10, my - 16))], fill=(110, 64, 36, 255))
        d.rectangle([S((mx - 14, my - 1)), S((mx + 14, my + 6))], fill=(196, 70, 62, 255))
        d.ellipse([S((hx - 13, hy - 9)), S((hx + 1, hy + 9))], fill=rig["skin"])   # пальцы поверх края кружки
    if prop == "stylus":
        d.line([S((hx - 12, hy - 30)), S((hx + 16, hy + 20))], fill=INK, width=8 * SS)
        d.line([S((hx - 11, hy - 28)), S((hx + 13, hy + 15))], fill=(150, 156, 176, 255), width=3 * SS)
        d.ellipse([S((hx - 9, hy - 9)), S((hx + 7, hy + 7))], fill=rig["skin"])
    out = big.resize((w + PAD * 2, h), Image.LANCZOS)
    a = out.getchannel("A").point(lambda v: 255 if v > 120 else 0)   # без полупрозрачной каши по краям
    out.putalpha(a)
    return out


def main():
    for slug, rig in RIGS.items():
        base = Image.open(os.path.join(CUT, f"{slug}_sitSide.png")).convert("RGBA")
        rig = {k: tuple(v) if isinstance(v, list) else v for k, v in rig.items()}
        e = rig["elbow"]
        # рисует: кисть на планшете, стилус ходит туда-сюда
        tab = (e[0] + 134, e[1] - 22)
        for i, (ox, oy) in enumerate([(0, 0), (8, -3), (3, 3)], 1):
            frame(base, rig, (e[0] + 126 + ox, e[1] - 36 + oy), "stylus", tab).save(os.path.join(CUT, f"{slug}_drawSide{i}.png"))
        # кофе: кружка на столе → на полпути → у рта
        m = rig["mouth"]
        for i, (hand, lift) in enumerate([((e[0] + 122, e[1] - 30), 0), (((e[0] + 122 + m[0] + 2) / 2, (e[1] - 30 + m[1] + 22) / 2), .5), ((m[0] + 2, m[1] + 22), 1)], 1):
            frame(base, rig, hand, "mug", lift=lift).save(os.path.join(CUT, f"{slug}_sipSide{i}.png"))
        print(slug, "ok")


if __name__ == "__main__":
    main()
