"""Сборка прототипа: studio.src.html + data.json → studio.html (один файл).

    python3 tools/build.py
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(HERE, "studio.src.html"), encoding="utf-8").read()
data = json.load(open(os.path.join(HERE, "data.json"), encoding="utf-8"))
cfg_path = os.path.join(HERE, "config.json")
if os.path.exists(cfg_path):   # свежий конфиг (роли, цвета, кто чей хозяин) — без пересъёмки таблицы
    data["config"] = json.load(open(cfg_path, encoding="utf-8"))
blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
import base64
bg_path = os.path.join(HERE, "assets", "studio-bg2.jpg")
bg = "data:image/jpeg;base64," + base64.b64encode(open(bg_path, "rb").read()).decode() if os.path.exists(bg_path) else ""
def uri(name, mime):
    path = os.path.join(HERE, "assets", name)
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode() if os.path.exists(path) else ""
amap = open(os.path.join(HERE, "assets", "atlas.json"), encoding="utf-8").read() if os.path.exists(os.path.join(HERE, "assets", "atlas.json")) else "{}"
out = (src.replace("__DATA__", blob).replace("__BG__", bg).replace("__ATLASMAP__", amap)
       .replace("__ATLAS__", uri("atlas.png", "image/png")).replace("__WHEEL__", uri("wheel.png", "image/png")))
open(os.path.join(HERE, "studio.html"), "w", encoding="utf-8").write(out)
head = '<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>'
open(os.path.join(HERE, "preview.html"), "w", encoding="utf-8").write(head + out + "</body></html>")
print("studio.html", len(out.encode()) // 1024, "KB")
