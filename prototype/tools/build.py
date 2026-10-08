"""Сборка прототипа: studio.src.html + data.json → studio.html (один файл).

    python3 tools/build.py
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(HERE, "studio.src.html"), encoding="utf-8").read()
data = json.load(open(os.path.join(HERE, "data.json"), encoding="utf-8"))
blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
out = src.replace("__DATA__", blob)
open(os.path.join(HERE, "studio.html"), "w", encoding="utf-8").write(out)
head = '<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>'
open(os.path.join(HERE, "preview.html"), "w", encoding="utf-8").write(head + out + "</body></html>")
print("studio.html", len(out.encode()) // 1024, "KB")
