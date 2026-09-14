# UNO Local — Live Creator / UnoLive — NEXT ITERATION

## 1. Цель итерации

Довести текущий `Live Creator` до согласованной рабочей концепции без добавления лишних функций.

Работа ведётся:

```text
Branch:   live-creator
Worktree: D:\UNO\Live-Creator
```

На этом этапе:

- не интегрировать изменения в `main`;
- не менять основной UNO Pro Advanced;
- не делать сборку, пока пользователь явно не скажет **«сделай сборку»**;
- сохранить общий визуальный стиль UNO Pro Advanced / UnoLive;
- не добавлять функции, отсутствующие в этом ТЗ.

---

## 2. Общая архитектура

Live Creator остаётся самостоятельным экспериментальным модулем, но проектируется как будущая часть **UnoLive**.

Слои:

```text
core
ui
controllers
devices
```

Общий `core` не должен зависеть от UNO Synth Pro, `.unosyp`, Launchpad или конкретного MIDI-контроллера.

UNO Synth Pro — первый device adapter.

Физические 8×8-контроллеры в будущем подключаются через controller profiles. GRID не должен содержать Launchpad-specific логику.

---

## 3. Глобальное системное хранилище UnoLive

Это правило относится **ко всему проекту**, а не только Live Creator.

Корневой каталог служебных данных:

```text
%LOCALAPPDATA%\UnoLive\
```

Получать путь через Windows environment/API. Имя пользователя и абсолютный путь не хардкодить.

Ориентировочная структура:

```text
%LOCALAPPDATA%\UnoLive\
├── settings\
├── state\
├── controllers\
├── devices\
├── cache\
└── logs\
```

Live Creator state может храниться, например:

```text
%LOCALAPPDATA%\UnoLive\state\live_creator_state.json
```

Все 64 песни и их параметры находятся в общем state.

### LOCAL PRESETS

Папка `LOCAL PRESETS` содержит **только пользовательские preset-файлы и пользовательские каталоги**.

Запрещено автоматически создавать там `Song`, `Songs`, `state.json`, `settings.json`, `logs`, `cache`, `controllers` или любые другие служебные файлы UnoLive.

Перемещение/удаление пользователем исходного `.unosyp` допускается. При сломанной ссылке показывать:

```text
PRESET NOT FOUND
```

Скрытые копии preset-файлов не создавать.

---

## 4. Основной экран

Один режим работы. Не возвращать переключение `CREATOR / LIVE`.

Основные области:

```text
┌────────────────────────────────────────────────────┐
│                   TIMELINE                         │
│                    01–32                           │
│                    33–64                           │
├──────────────┬───────────────────┬─────────────────┤
│   PRESETS    │      GRID 8×8     │    WORK AREA    │
│              │     64 SONGS      │                 │
└──────────────┴───────────────────┴─────────────────┘
```

Не добавлять декоративные заголовки, инструкции и debug-информацию.

---

## 5. GRID — 64 песни

GRID = `8 × 8 = 64 song pads`.

Каждый pad = отдельная песня.

У каждой песни собственные Timeline, блоки, markers, tempo, name, color и playback-related state/settings.

### Empty pad

Показывает только номер `01–64`.

Не показывать `Empty` или `Song 01`.

### Filled pad

После создания песни номер исчезает полностью. Показывается только имя песни.

Текст по центру, word-wrap по словам, несколько строк центрируются внутри pad, если не помещается — ellipsis.

Pads остаются **строго квадратными**.

---

## 6. Выбор песни во время playback

Выбор и playback — независимые состояния.

Если сейчас играет Song A и пользователь нажимает Song B:

```text
Song A → продолжает играть
Song B → становится selected
Timeline → показывает Song B
WORK AREA → показывает Song B
```

Song B автоматически не запускается. Playback Song A не прерывается.

---

## 7. Цвет song pad

Каждая созданная песня имеет persistent color.

Цвет песни и цвет Timeline Block — независимые свойства.

Отдельную кнопку `COLOR` из `WORK AREA` **убрать**.

Цвет песни меняется через ПКМ по song pad → `Color...`.

Открывается собственная тёмная popup-палитра UnoLive. Не использовать стандартный Windows Color Picker как основной интерфейс.

Палитра должна содержать достаточно подготовленных цветов/оттенков, а не только нынешние 7.

Изменение применяется сразу и сохраняется в state.

---

## 8. Контекстное меню song pad

ПКМ по song pad:

```text
Color...
────────────
Cut          Ctrl+X
Copy         Ctrl+C
Paste        Ctrl+V
────────────
Delete       Del
```

Для song pad **нет** `Set Marker`, `Delete Marker`, `Loop`.

`DEL` для выбранного song pad работает аналогично удалению выбранного Timeline Block.

Удаление song pad очищает песню/ячейку Live Creator, но **никогда не удаляет исходные `.unosyp` файлы**.

---

## 9. WORK AREA — свойства песни

WORK AREA содержит только song-level информацию и управление. Не возвращать прежнюю block-info section.

### PLAY

Обычная прямоугольная кнопка. PLAY находится сверху.

Исправить существующую ошибку, при которой PLAY после нажатия сразу «отскакивает».

Не угадывать причину — проверить реальный lifecycle playback state.

`Space` управляет playback, кроме ситуации ввода текста в text field.

### PLAY DELAY

Непосредственно под PLAY:

```text
PLAY DELAY    [ OFF ▼ ]
```

Допустимые значения строго:

```text
OFF
5 s
10 s
15 s
30 s
45 s
1 min
```

При PLAY начинается countdown. Повторная команда во время countdown отменяет его.

---

## 10. NAME

```text
NAME
[             Song Name             ]
```

Поле имени сделать **чуть шире**, чем сейчас.

Фон поля NAME окрашен в текущий цвет выбранной песни.

Текст выровнен **по центру**.

Цвет текста автоматически должен обеспечивать нормальный контраст с выбранным background.

Изменение цвета song pad немедленно меняет цвет NAME field.

---

## 11. TEMPO

Текущий layout исправить.

Не:

```text
TEMPO                         [120]
```

а:

```text
TEMPO   [120]
```

Поле компактное, примерно под трёхзначное значение.

---

## 12. Свойства времени песни

В WORK AREA добавить:

```text
DURATION    04:32
ELAPSED     01:47
REMAINING   02:45
```

### DURATION

Номинальная длительность всей песни.

Расчёт должен учитывать:

- TEMPO песни;
- структуру Timeline;
- длину блоков;
- **реальную длину секвенции используемого preset**.

Нельзя рассчитывать duration только по количеству Timeline blocks.

`DURATION` рассчитывается **без учёта Loop**.

### ELAPSED

Текущая позиция воспроизведения относительно структуры песни.

Во время Loop не накапливать бесконечное время повторов.

### REMAINING

Номинальное время от текущей позиции до конца структуры песни.

Все значения обновлять во время playback.

---

## 13. Остальные свойства WORK AREA

Оставить `STEPS`, `BLOCKS` и добавить `MARKERS`.

Ориентир:

```text
[ PLAY ]

PLAY DELAY   [ OFF ▼ ]

NAME
[           Song 02           ]

TEMPO   [120]

DURATION    04:32
ELAPSED     01:47
REMAINING   02:45

STEPS       18
BLOCKS       7

MARKERS
...
```

Не добавлять `COLOR button`, `STATUS / READY`, `NEW`, `OPEN`, `SAVE`, `SEND TO DEVICE`.

---

## 14. Timeline

Timeline всегда отображает выбранную песню.

Фиксированная структура:

```text
01 02 03 ... 31 32
──────────────────
Timeline row 1

33 34 35 ... 63 64
──────────────────
Timeline row 2
```

Всего `2 × 32 = 64 Song Steps`.

Весь Timeline должен помещаться без горизонтального scrolling.

Обе строки имеют одинаковый scale. Каждый Song Step имеет одинаковую фиксированную ширину.

Использовать тонкую slot grid. Можно немного усилить guides на `8/16/24/32` и `40/48/56/64`.

---

## 15. Blocks через границу 32/33

Один логический block может пересекать границу 32/33.

В UI он отображается двумя визуальными сегментами, но в data model это **ONE BLOCK**.

У него единые selection, color, preset, move, resize, delete, copy/cut и loop semantics.

---

## 16. EMPTY

EMPTY занимает **реальную ширину Song Steps** и не сжимается.

---

## 17. Drag preset → Timeline

При drag из LOCAL PRESETS показывать:

- drag ghost;
- snapped target;
- предполагаемую позицию;
- различие `INSERT` и `REPLACE` ещё до mouse release.

Drop between blocks = `INSERT` с ripple.

Drop onto block = `REPLACE` с сохранением длины заменяемого блока.

Максимум = `64 Song Steps`.

Если операция превышает лимит:

```text
64-step limit reached
```

Никакого автоматического truncation.

---

## 18. MOVE и RESIZE должны выглядеть по-разному

### MOVE

Grab за тело блока:

- move cursor;
- блок визуально отделяется;
- появляется semi-transparent ghost;
- ghost следует за mouse;
- snapping к Song Step grid;
- исходное положение можно приглушить;
- target position отчётливо виден.

### RESIZE

Grab точно за edge блока:

- horizontal resize cursor;
- блок остаётся anchored;
- двигается только соответствующая граница;
- активный edge имеет заметный vertical resize indicator;
- изменяемые slots визуально видны.

Не возвращать старые белые стрелки MOVE.

---

## 19. Timeline Block — контекстное меню

ПКМ по блоку:

```text
Set Marker
Delete Marker
────────────
Color...
────────────
Loop
────────────
Cut          Ctrl+X
Copy         Ctrl+C
Paste        Ctrl+V
────────────
Delete       Del
```

Недоступные команды должны быть disabled.

---

## 20. Cut / Copy / Paste блоков

Поддерживать `Ctrl+X`, `Ctrl+C`, `Ctrl+V`, `Del`.

### Copy

Копирует block data: preset reference, block length, block color и остальные block-specific параметры.

### Cut

То же + удаление исходного блока согласно Timeline editing semantics.

### Paste

Вставляет block в выбранную позицию Timeline с соблюдением INSERT/ripple и 64-step limit.

### Marker

**Marker никогда не входит в clipboard Timeline Block.**

---

## 21. Цвет Timeline Block

ПКМ → `Color...`.

Открывает ту же визуально согласованную UnoLive palette.

Block color независим от song color.

Изменение применяется сразу и сохраняется в state.

---

## 22. Markers — структурные секции песни

Marker — **не свойство одного блока**.

Marker обозначает **начало секции песни**.

Marker начинается на левом краю выбранного блока и его секция продолжается **до следующего Marker** либо до конца песни.

Поэтому один marker может охватывать любое количество последующих blocks.

---

## 23. Визуализация Marker

Над левым краем соответствующего Timeline Block:

```text
🚩 CHORUS
│
[ Block ]
```

Marker text не помещать внутрь preset block.

---

## 24. Marker context commands

ПКМ по соответствующему блоку:

```text
Set Marker
Delete Marker
```

`Set Marker` позволяет задать/редактировать текст, например `INTRO`, `VERSE 1`, `CHORUS`, `SOLO`, `OUTRO`.

Один marker на одну начальную позицию секции.

---

## 25. Удаление блока с Marker

При удалении блока, на котором начинается marker:

1. marker не должен случайно исчезать вместе с preset;
2. перенести marker на следующий существующий block;
3. если следующего block нет — удалить marker.

---

## 26. MARKERS в WORK AREA

Добавить компактную секцию:

```text
MARKERS

01   INTRO
05   VERSE 1
13   CHORUS
21   VERSE 2
29   CHORUS
41   SOLO
49   FINAL
```

Число слева = **Song Step начала секции**, а не порядковый номер marker.

Клик по marker выбирает/показывает соответствующее место Timeline и block, с которого начинается секция.

---

## 27. LOOP

Loop назначается через ПКМ Timeline Block → `Loop`.

Если выбран один block — Loop = этот block.

Если выбрана группа — Loop = от начала первого выбранного block до конца последнего выбранного block.

Selection и Loop Range — разные состояния.

---

## 28. Назначение Loop во время playback

Если playback сейчас находится до будущего Loop и пользователь назначает Loop, **не прыгать в Loop**.

Playback продолжает естественное движение.

Только когда playback сам доходит до начала Loop Range, диапазон начинает повторяться.

---

## 29. Выход из активного Loop

Во время активного зацикливания повторное нажатие `PLAY` означает:

```text
EXIT LOOP + CONTINUE
```

а **не STOP**.

После этого Loop снимается, playback не останавливается, позиция не сбрасывается, песня продолжает обычное движение дальше по Timeline.

---

## 30. Визуальные состояния Loop

Различать:

- Assigned Loop — назначен, playback ещё не дошёл;
- Active Loop — диапазон реально повторяется.

Не смешивать `Selection`, `Loop Range`, `Playback`.

---

## 31. Playback indication — исправить

Сейчас эффект практически не виден на цветных blocks и song pads. Это UX-баг.

Пульсация должна быть **явно заметной на любом цвете**, а не только на EMPTY.

Для Playing Timeline Block и Playing song pad использовать:

- заметное повышение brightness/fill;
- мягкую пульсацию;
- сохранение исходного цвета;
- стабильный читаемый текст.

Не использовать резкое blinking, исчезновение текста или moving playhead.

**Moving playhead вообще не нужен.**

---

## 32. Selected + Playing

Если объект одновременно selected и playing, оба состояния должны быть видны.

Например:

```text
orange selection border
+
brightness/pulse playback fill
```

Не заменять цвет песни/блока оранжевой заливкой.

---

## 33. Preset Browser

Dropdown:

```text
LOCAL PRESETS
HARDWARE PRESETS
```

Не возвращать `SONG PRESETS`.

LOCAL PRESETS: folder tree/library, `.unosyp`, selection, drag/drop в Timeline.

HARDWARE PRESETS: hardware preset/slot representation без небезопасных SysEx операций.

---

## 34. LOCAL PRESETS numbering

Оставить уже реализованную нумерацию:

```text
001   2w2
002   aboba3228
003   AltWood
...
```

Номер — отдельная компактная колонка и не является частью имени preset.

---

## 35. Multi-selection

Timeline должен поддерживать выбор группы blocks для операций, которым это необходимо, прежде всего Loop.

Marker section определяется соседними markers, а не selection.

---

## 36. MIDI / Hardware safety

Не придумывать MIDI/SysEx mapping.

Без подтверждённой hardware mapping запрещены STORE, destructive SysEx, изменение hardware SONG и отправка неизвестных команд.

`0x28 / STORE` остаётся locked.

Не менять SEQ ON/OFF без подтверждённой hardware mapping.

---

## 37. Что НЕ делать в этой итерации

Не добавлять:

- `.unosong`;
- отдельные song files;
- SONG PRESETS;
- NEW/OPEN/SAVE project workflow;
- SEND TO DEVICE;
- Launchpad-specific UI;
- физические controller mappings;
- white MOVE arrows;
- moving playhead;
- отдельную COLOR button в WORK AREA;
- block-info panel;
- STATUS/READY;
- декоративные controls;
- скрытые копии `.unosyp`.

---

## 38. Regression requirements

Проверить минимум:

1. GRID остаётся 8×8.
2. Все pads квадратные.
3. Empty pads показывают только `01–64`.
4. Filled pads показывают только song name.
5. Выбор другой песни не прерывает playback.
6. Timeline переключается на selected song.
7. Timeline = ровно 64 steps, 32+32.
8. EMPTY имеет правильную slot width.
9. Block через 32/33 остаётся одним логическим block.
10. Drag preset корректно показывает INSERT/REPLACE.
11. MOVE визуально отличается от RESIZE.
12. `Del` удаляет selected block.
13. `Del` работает для selected song pad согласно его semantics.
14. `Ctrl+X/C/V` работают.
15. Marker не копируется вместе с block.
16. Marker section продолжается до следующего marker.
17. MARKERS отображаются в WORK AREA.
18. Loop одного блока работает.
19. Loop группы blocks работает.
20. Назначение Loop во время playback не вызывает jump.
21. При достижении Loop он активируется.
22. PLAY внутри активного Loop снимает Loop и продолжает песню.
23. DURATION не меняется из-за Loop.
24. Playback pulse хорошо виден на цветном block.
25. Playback pulse хорошо виден на цветном song pad.
26. Selected + Playing одновременно различимы.
27. Song Color меняется через ПКМ.
28. Block Color меняется через ПКМ.
29. NAME field имеет цвет выбранной песни.
30. NAME text центрирован.
31. TEMPO input расположен рядом с TEMPO.
32. State сохраняется в `%LOCALAPPDATA%\UnoLive\`.
33. В LOCAL PRESETS не создаются системные файлы.
34. Никаких destructive MIDI/SysEx команд не отправляется.

---

## 39. Критерий готовности

Итерация считается готовой, когда интерфейс можно использовать как цельную рабочую поверхность:

```text
выбрал Song
→ собрал Timeline из presets
→ расставил секции Markers
→ назначил цвета
→ запустил playback
→ видишь реальное движение по подсветке
→ заранее назначил Loop
→ дошёл до Loop
→ повторил участок
→ PLAY
→ песня пошла дальше
```

При этом UI должен оставаться **простым и функциональным**: постоянные элементы только для постоянно используемых функций, объектные операции — через ПКМ и стандартные hotkeys.

**Сборку после выполнения ТЗ не делать автоматически.** Сначала показать результат/изменения и дождаться отдельной команды пользователя на сборку.
