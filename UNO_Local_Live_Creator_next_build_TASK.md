# Live Creator — следующая сборка после v0.2-alpha
## Задание для UNO Local

Работать только в `D:\UNO\Live-Creator`, ветка `live-creator`.
Не изменять `D:\UNO\project_unified` и `main`.
Текущая база: `v0.2-alpha`.

## Компоновка
```text
┌──────────────────────────────────────────────────────────────────┐
│ TIMELINE — на всю ширину, примерно на 1/3 ниже текущего         │
├──────────────────┬────────────────────────┬──────────────────────┤
│ PRESETS          │ GRID 8×8               │ WORK AREA            │
│                  │                        │                      │
└──────────────────┴────────────────────────┴──────────────────────┘
```
- PRESETS оставить такой же ширины и геометрии, как сейчас в v0.2-alpha.
- WORK AREA сделать строго той же ширины, что PRESETS.
- GRID занимает центральное пространство.
- TIMELINE растянуть практически от края до края.

## UI / тема
Использовать реальный визуальный стиль UNO Pro Advanced как source of truth.
Убрать стандартный внешний вид Windows/Tk/ttk, особенно scrollbar, dropdown, buttons и inputs.
Тёмная тема UNO, серые границы, бело-серый текст, оранжевый active/selected accent.
Если системный widget нельзя нормально стилизовать — использовать custom control.
Не добавлять декоративные заголовки, инструкции и элементы без назначения.

## PRESETS
В режиме CREATOR dropdown содержит только:
- LOCAL PRESETS
- HARDWARE PRESETS

LOCAL: существующая локальная библиотека `.unosyp`, папки, выбор, drag/drop в TIMELINE.
HARDWARE: аппаратные пресеты UNO Synth Pro.

`SONG PRESETS` в CREATOR не добавлять.
Работа с песнями относится к режиму LIVE, как было задумано ранее.

## CREATOR / LIVE
Компактный переключатель `CREATOR | LIVE` разместить справа над/в верхней зоне TIMELINE, без отдельной большой панели.
Это режим страницы, а не конкретного MIDI-контроллера.

## GRID 8×8
Убрать верхний и правый функциональные ряды, имитировавшие Launchpad.
Оставить только чистую квадратную матрицу 8×8 = 64 Song Steps.
Не имитировать корпус конкретного контроллера.

TIMELINE и GRID используют одну arrangement model:
- выбор в TIMELINE отражается на GRID;
- выбор pad отражается в TIMELINE;
- playhead синхронизирован;
- отдельной модели GRID нет.

## Контроллеры
Физические 8×8 MIDI-контроллеры в будущем подключаются через `Settings → Controllers → Profiles`.
Launchpad Mini MK3 — лишь один из будущих профилей наряду с другими 8×8 и Generic 8×8 MIDI.
Core/Grid не должны зависеть от конкретного контроллера.
Не придумывать Note/CC mappings.
Для Launchpad использовать только официальную документацию Novation:
https://userguides.novationmusic.com/hc/en-gb/sections/23731330371602-Launchpad-Mini-User-Guide

## WORK AREA
Состав сверху вниз:
```text
NEW   OPEN   SAVE

      [ ▶ / ■ ]

TEMPO     [120] BPM

12 / 64 · Bass01
```
- NEW / OPEN / SAVE — верхняя строка, компактно.
- PLAY/STOP — одна квадратная кнопка.
- stopped = `▶`, playing = `■`.
- TEMPO — глобальный tempo песни.
- `12 / 64 · Bass01` — компактный current status.
- Не добавлять отдельные FROM HERE, LOOP, PREV/NEXT и т.п.

## PLAY FROM SELECTION
- Если выделен блок/позиция TIMELINE — PLAY стартует с выделенного места.
- Если выбран pad GRID — PLAY стартует с соответствующего Song Step/блока.
- Если ничего не выделено — с начала.
- PLAY/STOP остаётся одной кнопкой.

## Selection / Loop
Поддержать одиночное и множественное выделение блоков.
TIMELINE и GRID используют одно selection state.

Архитектурно:
`Selection != Playhead != Loop Range`

Выбор нового блока во время playback не должен сам переносить playhead.

Отдельную LOOP-кнопку не добавлять.
LOOP задаётся через `Shift + Right Click` для выделенных блоков.
Loop Range: от начала первого выбранного блока до конца последнего.
При активном loop PLAY циклически воспроизводит диапазон.

## TIMELINE
Сохранить ранее утверждённую модель:
- максимум 64 Song Steps;
- Preset Block = 1+ последовательных steps;
- номера шагов вычисляются динамически;
- диапазоны над блоками: `01–03`, `04–05`, `06`;
- drop между блоками = INSERT;
- drop на блок = REPLACE с сохранением длины;
- resize правой границей;
- move/resize используют ripple editing и пересчитывают всё последующее;
- EMPTY = узкий gap;
- движение вправо может создавать EMPTY, влево — уменьшать/убирать;
- превышение 64 steps отклоняется с `64-step limit reached`;
- ничего не обрезать автоматически;
- старую 4×16 arrangement grid не возвращать.

Не создавать кнопочный дубль операций TIMELINE вокруг GRID (`−`, `+`, `←`, `→`, `EMPTY`, `UNDO`, `REDO`, `DELETE`).

## Архитектура
Сохранять `core / ui / controllers / devices`.
Generic Core не зависит от UNO, `.unosyp`, `.unosong`, Launchpad или конкретного controller.
UNO Synth Pro = device adapter.
Физические grid controllers = controller adapters/profiles.
GUI не содержит hardware-specific business logic.

## MIDI safety
Не выдумывать MIDI/SysEx/Note/CC mapping.
STORE / `0x28` остаётся locked.
Не менять SEQ ON/OFF без подтверждённого mapping.
Diagnostics не должны посылать destructive commands.
Software test / IMPLEMENTED != HARDWARE PASS.

## .unosong
Не ломать принятую архитектуру:
- внутренний self-contained формат;
- не официальный IK song format;
- future container: manifest + arrangement + embedded original raw `.unosyp`;
- raw сохранять byte-for-byte;
- internal `preset_id`, не hardware slots 1–256;
- identical raw data можно dedupe SHA-256;
- hardware SONG — возможный deployment backend, не source of truth.
Полную реализацию контейнера не делать только ради этой UI-итерации, если она не требуется.

## Критерий готовности
Должны быть видны и работать:
1. компактный full-width TIMELINE;
2. PRESETS | GRID 8×8 | WORK AREA;
3. PRESETS и WORK AREA одинаковой ширины;
4. только чистая 8×8 grid;
5. Creator dropdown: LOCAL/HARDWARE;
6. NEW/OPEN/SAVE сверху WORK AREA;
7. одна квадратная PLAY/STOP;
8. TEMPO и compact current status;
9. PLAY с выделенного места;
10. multi-selection;
11. Shift+Right Click loop;
12. Selection/Playhead/Loop Range разделены;
13. единая тема UNO, включая scrollbars/dropdowns;
14. никаких лишних надписей;
15. main не затронут.

После реализации выполнить software/regression checks и собрать следующую standalone версию Live Creator.
В отчёте указать изменённые файлы, реализованные функции, проверки, оставшиеся заглушки, путь к сборке и commit hash (если commit сделан).
Не заявлять HARDWARE PASS без реального hardware test.
