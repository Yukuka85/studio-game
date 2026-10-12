# Фон студии — промт и ТЗ

Фон — одна картинка студии **без людей**. Человечки, кружки, бумаги, кот и карточки на доске — отдельные объекты игры, они рисуются поверх.

Схема расстановки: [layout-guide.png](layout-guide.png). Это наша сцена из прототипа, 320×256 точек, увеличена в 4 раза. Её прикладываем к промту как образец композиции.

---

## 1. Промт для нейросети (английский)

Подходит для Midjourney, ChatGPT (генерация картинок), Ideogram и Retro Diffusion. Лучше всего — приложить `layout-guide.png` и попросить «перерисуй эту планировку в таком стиле».

```
Cozy pixel art illustration of a small creative agency studio in the evening, empty room, no people.
High three-quarter top-down camera (about 60 degrees), one-point perspective: back wall in the center,
both side walls recede toward the viewer. Frame 5:4.

Mood and palette: deep indigo and navy walls, dark blue carpet with a slightly lighter rug in the center,
warm honey-orange wooden desks as the main warm accent, glowing cyan monitor screens, cool light from tall
windows on both side walls, warm desk lamps, a soft pool of light in the middle of the floor, darker corners.
Dark navy pixel outlines (not black), limited palette of about 32 colors, crisp readable pixel clusters,
cozy indie game background, lots of small lived-in details: cables, papers, sticky notes, coffee mugs,
headphones, PC towers, desk drawers, plants.

Layout, keep exactly:
- Back wall center: a large blank whiteboard in a wooden frame with a marker tray, nothing written on it.
- Back wall left: wall-mounted TV with a dark screen, a small strawberry poster next to it, a light switch.
- Back wall right: two small framed posters, a round wall clock, a shelf with books, small golden trophies
  and a small smart speaker.
- Back-left corner: desk against the back wall with two large monitors facing the viewer, a desk lamp,
  an empty office chair in front of the desk seen from behind.
- Back-right corner: coffee counter with an espresso machine and cups, a water cooler next to it.
- Left wall: a long desk running along the wall in perspective, angled monitor, desk lamp, empty chair;
  a wooden door further down the left wall; a tall window above the desk.
- Right wall: the same desk along the wall, mirrored, with a tall window.
- Center: a long wooden desk facing the viewer, two empty chairs on its far side, two monitors at the left
  and right ends with their backs to the viewer, a desk lamp in the middle.
- Front center: a long double desk, two monitors on it with screens facing the viewer, two empty chairs in
  front of it seen from behind, two PC towers under the desk.
- Bottom-left: a big potted plant cut off by the frame edge, an orange bean bag chair, a printer on a small
  cabinet near the left wall.
- Bottom-right: a purple sofa seen from behind (backrest toward the viewer) with a low coffee table in front
  of it, a potted plant cut off by the frame, a cardboard promoter standee near the right wall.
- Bottom center: a small trash bin full of crumpled paper, a small potted plant.
```

**Негативный промт** (там, где он есть):
```
people, characters, animals, text, letters, logos, watermark, signature, photorealistic, 3d render,
isometric diamond grid, fisheye, cubicles, grey corporate office, white walls, daylight, blurry,
smooth airbrush gradients, noise, jpeg artifacts
```

**Настройки:**
- **Midjourney:** `--ar 5:4 --style raw`. `layout-guide.png` — как картинку-образец, в начало промта.
- **ChatGPT:** приложить `layout-guide.png` и написать «Redraw this exact layout as…» + промт выше.
- **Retro Diffusion:** размер 320×256 — тогда пиксель получится настоящий, по сетке. Остальные генераторы рисуют «под пиксель», такую картинку придётся чистить.

**Важно про права:**
- Референс с Pinterest не подкладывать как образец стиля в финальную генерацию: автор неизвестен. Для пробы — можно, для продукта — нет.
- Перед коммерческим использованием проверить условия сервиса: у Midjourney и ChatGPT права на результат у пользователя на платном тарифе.

---

## 2. ТЗ художнику (или для доводки нейросетевой картинки)

**Размер:**
- 320×256 игровых пикселей, 1 пиксель картинки = 1 игровой пиксель.
- Сдать в оригинале и в ×4 (1280×1024), PNG без сжатия.

**Камера и стиль:**
- Как на схеме: вид сверху под углом, задняя стена по центру, боковые стены уходят к зрителю.
- Палитра до ~32 цветов: индиго и тёмно-синий, тёплое дерево, циан экранов.
- Обводка тёмно-синяя `#121330`, не чёрная.

**Слои (отдельные PNG с прозрачностью, все 320×256 и строго совмещённые):**
1. `01_room` — пол, стены, окна, дверь, ковры, всё, что на стенах. Доска пустая: карточки на ней живые, их рисует игра.
2. `02_back` — мебель, которая всегда за людьми: столы и мониторы, тумбы, кофейный угол, кулер, принтер, диван (сиденье), журнальный столик.
3. `03_front` — то, что перекрывает людей:
   - передние стенки столов, за которыми сидят лицом к нам;
   - спинка дивана;
   - передняя часть кресла-мешка.
4. `04_foreground` — крупные растения на переднем плане, обрезанные краем.
5. `05_glow` — светящиеся места: экраны, лампы, окна, телевизор. Игра включает и выключает свет по времени суток.

**Отдельные спрайты:**
- офисный стул вид сзади и вид спереди (их отодвигают, когда человек встаёт);
- монитор включён / выключен.

**Места, где сидят и стоят люди** — пиксели в нашей сетке 320×256, левый верхний угол человечка 20×16 (сидит) или 20×20 (стоит). Мебель должна оставлять эти места свободными:

| Место | Точка | Поза |
|---|---|---|
| Угловой стол у задней стены | 56, 74 | сидит спиной к нам |
| Стол у левой стены | 22, 110 | спиной, лицом к стене |
| Центральный стол, слева | 124, 90 | лицом к нам, за столом |
| Центральный стол, справа | 172, 90 | лицом к нам |
| Передний стол, слева | 120, 178 | спиной к нам |
| Передний стол, справа | 178, 178 | спиной к нам |
| Стол у правой стены | 278, 110 | спиной, лицом к стене |
| Штурм у доски | 114–184, 63 | 4 человека стоят спиной |
| Кофейный угол | 228, 70 / 248, 74 / 264, 84 | стоят |
| Диван | 240 / 262 / 284, 208 | сидят спиной к нам |
| Кресло-мешок | 36, 198 | сидит лицом к нам |

**Не рисовать:** людей, животных, текст, логотипы. Кружки, бумаги и кота игра рисует сама.

**Права:**
- Полная передача прав с возможностью использования в коммерческом продукте (SaaS).
- Исходники в Aseprite или PSD со слоями.
