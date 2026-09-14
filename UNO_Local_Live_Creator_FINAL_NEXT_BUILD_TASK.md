# Live Creator — финальное ТЗ следующей сборки для UNO Local

**Это ТЗ полностью заменяет предыдущие task-файлы.**

## Работа
Работать только в `D:\UNO\Live-Creator`, ветка `live-creator`. Текущая база — `v0.2-alpha`.
Не изменять `D:\UNO\project_unified` и `main`.

## Новая модель
- Один единый рабочий режим. `CREATOR/LIVE` отменены.
- GRID 8×8 = 64 независимых песни, а не 64 шага одной песни.
- Каждый pad имеет собственные: Timeline, tempo, name, color, blocks, EMPTY, loop/settings.
- Клик pad выбирает песню и показывает её Timeline сверху.
- Если играет другая песня, клик другого pad только меняет selection/editor context: playback не прерывается и новая песня не запускается.
- От `SONG PRESETS`, отдельных `.unosong` и отдельных song-файлов отказаться.
- Все 64 песни и параметры хранить в одном общем Live Creator settings/state file.
- Не создавать скрытые копии локальных `.unosyp`; хранить ссылки/идентификаторы. Если файл исчез — корректно показать `PRESET NOT FOUND`.

## Layout
```text
┌───────────────────────────────────────────────────────────────┐
│               TIMELINE ВЫБРАННОЙ ПЕСНИ                      │
├──────────────────┬──────────────────────┬─────────────────────┤
│ PRESETS          │ GRID 8×8             │ WORK AREA           │
└──────────────────┴──────────────────────┴─────────────────────┘
```
- Timeline практически на всю ширину.
- PRESETS оставить такой же ширины/геометрии, как в v0.2-alpha.
- WORK AREA строго той же ширины, что PRESETS.
- GRID занимает центр.
- Важное уточнение: примерно на 1/3 уменьшить прежде всего **высоту самих Preset Blocks** относительно v0.2-alpha.
- EMPTY и строку диапазонов сделать соответственно компактнее.
- Timeline container подогнать под компактную дорожку без большого пустого вертикального пространства.
- Горизонтальный масштаб Song Steps из-за этого не менять.

## PRESETS
Dropdown содержит только:
- `LOCAL PRESETS`
- `HARDWARE PRESETS`

LOCAL: существующая `.unosyp` библиотека, folders, selection, drag/drop в Timeline.
HARDWARE: аппаратные presets UNO Synth Pro.
`SONG PRESETS` не добавлять.

## GRID
- Только чистые 8×8 pads. Без верхнего/правого ряда Launchpad и без корпуса конкретного controller.
- Empty pad — нейтральный тёмный.
- Pad с песней получает persistent color.
- Selected pad — border/overlay поверх собственного цвета.
- Playing pad — отдельный playback border/indicator; основной цвет не заменять.
- На pad: маленький номер `01..64` + короткое имя песни.
- Длинное имя — ellipsis; tooltip может показывать полное имя/tempo/duration.
- Изменение song name сразу отражается на pad.

## Цвета Timeline blocks
- Preset blocks тоже цветные и persistent.
- Разные presets различаются цветом.
- Одинаковый preset внутри одной песни желательно показывать одинаковым цветом.
- Selection и playhead показывать overlay/border, не заменяя основной цвет.
- EMPTY — нейтральный/тёмный.

## Timeline model
Для каждой песни:
- максимум 64 Song Steps;
- block = 1+ последовательных steps;
- динамические диапазоны `01–03`, `04–05`, `06`;
- drop между blocks = INSERT;
- drop на block = REPLACE с сохранением длины;
- ripple editing;
- EMPTY = узкий gap;
- >64 steps: отклонить операцию и показать `64-step limit reached`; не обрезать;
- старую 4×16 arrangement grid не возвращать.

## MOVE / RESIZE
Отдельные `← → − +` не нужны.
- Возле левой/правой стороны block, но не на самой границе: hover показывает **белую полупрозрачную стрелку** в соответствующую сторону; drag = MOVE.
- Непосредственно на границе block: resize cursor/indicator; drag = растянуть/сжать.
- MOVE вправо может создавать EMPTY перед block.
- MOVE влево уменьшает существующий EMPTY; при нуле EMPTY исчезает.
- Сохранять ripple-логику последующих blocks.

## Selection / LOOP
- Поддержать single и multi-selection blocks.
- `Selection != Playhead != Loop Range`.
- Выбор другого block/pad не должен автоматически переносить playhead.
- Отдельной LOOP button нет.
- `Shift + Right Click` по/для предварительно выделенных blocks задаёт Loop Range от начала первого выбранного до конца последнего.
- При active loop playback циклически воспроизводит этот range.

## WORK AREA
WORK AREA = song editor + informer + transport + contextual block section.
Не дублировать операции Timeline.
Не добавлять `NEW / OPEN / SAVE`, `CREATOR/LIVE`, FROM HERE, PREV/NEXT или отдельную LOOP button.

Song-level минимум:
- `NAME` — editable;
- `TEMPO` — tempo выбранной песни;
- `DURATION` — рассчитанное время;
- `STEPS` — число используемых steps;
- `BLOCKS` — число preset blocks;
- `PLAY DELAY`;
- compact playback/current status.

Если выбран Timeline block, ниже можно показывать contextual block information/editor. Он **не заменяет** song-level section. Не придумывать лишние block parameters без необходимости.

## PLAY / STOP
- Одна обычная **прямоугольная** кнопка.
- stopped → `PLAY`;
- playing → `STOP`;
- повторное нажатие останавливает playback.
- `Space` = PLAY/STOP. Если фокус в текстовом поле и пробел нужен для ввода текста, hotkey не должен мешать.

Start:
- выбран block Timeline → старт с начала этого block;
- block не выбран → старт с начала песни выбранного pad.

Клик другого pad во время playback только меняет editor selection, не playback.

## PLAY DELAY
Dropdown:
`OFF | 5 s | 10 s | 15 s | 30 s | 45 s | 1 min`

Default = OFF.
При PLAY/Space с delay запускается countdown, затем playback.
Повторный PLAY/STOP или Space во время countdown отменяет запуск.
Countdown показать компактно.

## Хранение
Один общий state/settings:
```text
LiveCreatorState
├── global_settings
├── controller settings/profiles
└── pads[64]
    ├── name
    ├── color
    ├── tempo
    ├── timeline
    ├── loop/settings
    └── other song state
```
Не плодить отдельные song files на диске.

## SEND TO DEVICE
В будущем выбранную pad/song можно deploy/export в hardware SONG UNO Synth Pro.
Это не отдельный song file и не source of truth.
**В этой сборке SEND TO DEVICE не добавлять/не реализовывать**, пока нет подтверждённого безопасного hardware mapping.

## UI Theme
UNO Pro Advanced = source of truth.
- dark theme;
- UNO panel shades/borders;
- white/gray text;
- orange active/selected accent там, где соответствует теме;
- единые hover/active/disabled states;
- единая typography/spacing.
Исправить системно выглядящие Tk/ttk/Windows scrollbar, dropdown, buttons, inputs, tree/list, spin controls.
Не оставлять светлые стандартные Windows widgets. Если нормально стилизовать нельзя — custom themed control.
Не добавлять декоративные headings, debug instructions и элементы без конкретного назначения.

## Controllers
GUI GRID универсален.
Будущие physical 8×8 controllers подключаются через `Settings → Controllers → Profiles`.
Launchpad Mini MK3 — только один из будущих profiles; также возможны другие 8×8 и Generic 8×8 MIDI.
Core/Grid не зависят от конкретного controller.
Не придумывать Note/CC mappings.

## Architecture / Safety
Сохранять `core / ui / controllers / devices`.
Generic Core не зависит от UNO, `.unosyp`, Launchpad или конкретного MIDI controller.
UNO = device adapter; physical grids = controller adapters/profiles.
Не выдумывать MIDI/SysEx/Note/CC.
STORE / `0x28` locked.
Не менять SEQ ON/OFF без подтверждённого mapping.
Diagnostics не отправляют destructive commands.
`IMPLEMENTED`/software test != `HARDWARE PASS`.

## Отменённые старые решения
Не реализовывать:
- GRID = 64 steps одной песни;
- CREATOR/LIVE switch;
- SONG PRESETS;
- отдельные `.unosong`;
- NEW/OPEN/SAVE для песен;
- Launchpad top/right function buttons;
- квадратную PLAY/STOP;
- отдельный STOP;
- кнопочный дубль move/resize вокруг GRID.

## Критерий готовности
1. Один режим.
2. Timeline выбранной pad/song сверху.
3. Blocks примерно на 1/3 ниже v0.2-alpha; без лишней вертикальной пустоты.
4. PRESETS | GRID | WORK AREA; PRESETS и WORK AREA симметричны по ширине.
5. GRID = 64 independent songs.
6. Pad selection меняет Timeline, но не прерывает playback.
7. Persistent pad colors + number + short name; selected/playing states различимы.
8. Persistent colored Timeline blocks.
9. PRESETS = LOCAL/HARDWARE.
10. WORK AREA: name, tempo, duration, steps, blocks, delay, status + contextual block area.
11. Одна прямоугольная PLAY/STOP + Space.
12. PLAY from selected block, иначе from selected song start.
13. Delay OFF/5/10/15/30/45/60 sec с cancel.
14. Multi-selection + Shift+Right Click loop.
15. Selection/Playhead/Loop Range разделены.
16. MOVE translucent arrows near edges; exact edge = RESIZE.
17. MOVE создаёт/убирает EMPTY согласно правилам.
18. Ripple + 64-step limit на каждую песню.
19. Один общий settings/state file; без отдельных song files.
20. UNO theme применяется ко всем controls.
21. main/project_unified не затронуты.
22. Никаких неподтверждённых MIDI/hardware функций.

## После реализации
Выполнить software/regression checks и собрать следующую standalone версию.
В отчёте указать:
- изменённые файлы;
- реализованные функции;
- оставшиеся заглушки;
- выполненные проверки и результаты;
- точный путь к сборке;
- commit hash, если commit сделан.
Не заявлять HARDWARE PASS без реального hardware test.
Не добавлять функции вне этого ТЗ без необходимости.
