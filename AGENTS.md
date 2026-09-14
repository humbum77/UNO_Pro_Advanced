# Live Creator — актуальные правила

Работать только в `D:\UNO\Live-Creator`, ветка `live-creator`.
`D:\UNO\project_unified` и `main` не изменять.
Текущая standalone-версия: **v0.4-alpha**.
Перед работой целиком читать `UNO_Local_Live_Creator_FINAL_NEXT_BUILD_TASK.md`.
Это итоговое ТЗ полностью заменяет прежние task-файлы. Документы v0.1–v0.3 и старые сборки — история, не актуальная архитектура.

## Согласованная модель

- Один режим. Grid 8×8 = 64 независимые песни, НЕ шаги одной песни.
- Каждая песня: timeline до 64 steps, имя, tempo, persistent pad/block colors, EMPTY, loop и delay.
- Editor selection, playing song, playhead и loop — отдельные состояния. Выбор другого pad не прерывает playback и не запускает другую песню.
- Один `LiveCreatorState.json` рядом с launcher: все песни, global settings и controller settings.
- Только ссылки на оригинальные `.unosyp`, никаких embedded/скрытых копий. Отсутствующий файл: `PRESET NOT FOUND`.
- Не возвращать `.unosong`, SONG PRESETS, NEW/OPEN/SAVE, CREATOR/LIVE и внешние ряды Launchpad.

## Геометрия и управление

Timeline на всю ширину; блоки высотой 44 px вместо 66 px v0.2, горизонтальный масштаб сохранён.
PRESETS и WORK AREA — по 260 px; чистая 8×8 grid в центре.
UNO palette, тёмные inputs/dropdown, custom scrollbar/buttons; без дополнительных декоративных контролов.
DROP между блоками = INSERT, внутрь = REPLACE с сохранением длины.
MOVE/RESIZE — drag; белые полупрозрачные hover-стрелки возле сторон, точная граница = resize.
Ripple с EMPTY; превышение 64 отклонять целиком, не обрезать.
Multi-selection: Ctrl/Shift-click. Shift-right-click задаёт/снимает loop по выделению.
Одна прямоугольная PLAY/STOP, Space вне текстовых полей.
Старт с начала выбранного блока, иначе начала песни; active loop ограничивает диапазон.
Delay OFF/5/10/15/30/45/60 секунд, повторный PLAY/Space отменяет countdown.

## Архитектура и безопасность

Сохранять `core / ui / controllers / devices`. Generic core не зависит от UNO, `.unosyp` или конкретного controller.
`core/session.py` — 64 песни и независимый transport context. `core/state.py` — единый JSON, атомарная запись; повреждённый state не перезаписывать автоматически.
Редактирование структуры играющей песни останавливает её software transport и сбрасывает loop — унаследованное правило. Selection этого не делает.
Playback пока визуальный: один условный beat на Song Step. DURATION — оценка этой модели, не длительность UNO sequence.
HARDWARE PRESETS — заглушка. Physical profiles не подключены. SEND TO DEVICE не добавлять.
Не выдумывать MIDI/SysEx/Note/CC. STORE/0x28 locked; SEQ ON/OFF без mapping не трогать.
`IMPLEMENTED`, `SOFTWARE PASS`, `HARDWARE PASS` различать. Hardware pass только после проверки реального железа.

## Проверки и сборка

Сборка только по явному запросу. Текущий workflow — standalone **source release** для Python 3.10+ с Tkinter, не автономный EXE.
Перед упаковкой: compile/import, unittest regression, Tk GUI smoke, git diff --check, проверка ветки и состава изменений.
`tests/build_live_creator.py` собирает versioned directory + ZIP в `builds`, проверяет CRC/SHA-256 manifest и записывает BUILD_COMMIT.
Не включать пользовательский state, presets, caches или временные captures. Исторические сборки не менять.
Обновлять документацию каждого релиза: `Docs/LIVE_CREATOR_v0.4-alpha.md`.
