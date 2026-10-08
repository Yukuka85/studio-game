"""Снимок таблицы «Студия — статус» для прототипа (только чтение).

    uv run --directory ~/.claude/tools/studio-sheets-api python \
        ~/projects/Rabota/studio-game/prototype/tools/snapshot.py > ~/projects/Rabota/studio-game/prototype/data.json
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.expanduser("~/.claude/tools/studio-sheets-api"))
from sheets import values  # noqa: E402
import office  # noqa: E402  — палитры и шаблоны портретов

SECTIONS = {"В РАБОТЕ": "work", "ПАУЗА": "pause", "ВЫИГРАЛИ": "won",
            "ПРОИГРАЛИ И ЯМА НЕИЗВЕСТНОСТИ": "lost", "ОТПУСКА": "vacation"}
SHORT = {"Вадим Кампель": "Вадим", "Даниил Гудков": "Даня", "Алёна Мельник": "Алёна", "Юлия Кочебина": "Юля",
         "Оксана Моисеева": "Оксана", "Татьяна Хина": "Таня", "Фриланс": "Фриланс"}


def num(s):
    try:
        return float(str(s).replace(",", ".").replace("−", "-"))
    except ValueError:
        return 0.0


def main():
    d = values(["Неделя!B4:AB399", "Команда!B5:G11", "Проекты!B5:O200"])
    week, team, projects_sheet = d["Неделя!B4:AB399"], d["Команда!B5:G11"], d["Проекты!B5:O200"]
    dates = week[0][7:27]
    year = 2026
    days = []
    for s in dates:
        dd, mm = s.split(".")
        days.append(datetime.date(year, int(mm), int(dd)).isoformat())

    people = []
    tpl = {n: (colors, head) for n, _, colors, head in office.PEOPLE}
    for row in team:
        name = row[0]
        colors, head = tpl.get(name, (None, None))
        people.append({"name": name, "short": SHORT.get(name, name.split()[0]), "role": row[1], "group": row[2],
                       "colors": colors, "head": head, "plaid": name in office.PLAID})
    people.append({"name": "Фриланс", "short": "Фриланс", "role": "Внешние", "group": "Фриланс",
                   "colors": None, "head": None, "plaid": False})

    extra = {}
    for r in projects_sheet:
        r = r + [""] * 14
        extra.setdefault(r[2], {"type": r[1], "stage": r[3], "deadline": r[5], "budget": r[7], "csd": r[8],
                                "manager": r[9], "status": r[11], "chat": r[12]})

    projects, section = [], None
    for row in week[11:]:
        row = row + [""] * 27
        b, c, dcol, e, f, g, h = row[:7]
        if b in SECTIONS and not any(row[1:7]):
            section = SECTIONS[b]
            continue
        if not b:
            continue
        if not dcol and (c or e or f or g or h or not projects or projects[-1]["name"] != b):
            if projects and projects[-1]["name"] == b:
                continue
            ex = extra.get(b, {})
            projects.append({"name": b, "section": section, "manager": c, "stage": e or ex.get("stage", ""),
                             "status": f, "deadline": g, "budget": h or ex.get("budget", ""),
                             "type": ex.get("type", ""), "chat": bool(ex.get("chat")), "team": {}, "notes": {}})
            continue
        if dcol and not (projects and projects[-1]["name"] == b):
            projects.append({"name": b, "section": section, "manager": "", "stage": "", "status": "", "deadline": "",
                             "budget": "", "type": "", "chat": False, "team": {}, "notes": {}})
        if dcol:
            hrs = [num(x) for x in row[7:27]]
            projects[-1]["team"][dcol] = hrs
            if f:
                projects[-1]["notes"][dcol] = f
    in_week = {p["name"] for p in projects}
    inbox = [{"name": n, "stage": ex["stage"], "deadline": ex["deadline"], "manager": ex["manager"]}
             for n, ex in extra.items()
             if n not in in_week and ex["stage"] in ("Бриф", "Креатив", "Дизайн", "Защита", "Правки")]
    out = {"snapshot": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"), "days": days,
           "people": people, "projects": projects, "inbox": inbox}
    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
