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
print("studio.html", len(out.encode()) // 1024, "KB")
