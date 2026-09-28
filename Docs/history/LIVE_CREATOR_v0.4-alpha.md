# Live Creator v0.4-alpha

## Основание и запуск

Реализовано `UNO_Local_Live_Creator_FINAL_NEXT_BUILD_TASK.md`, заменяющее прежние задания.
Рабочая линия: `D:\UNO\Live-Creator`, `live-creator`. Предыдущий релиз — v0.3-alpha; геометрический reference — v0.2-alpha.
Основной UNO Pro Advanced и main не изменяются.
Это отдельное приложение: **source release**, как предыдущие alpha, не EXE с включённым Python.
Требуется Python 3.10+ с Tkinter. Запуск `run_live_creator.bat` или `python -m live_creator` из папки сборки.
Поставка: `builds/Live_Creator_v0.4-alpha/` и `builds/Live_Creator_v0.4-alpha.zip`.
Точный commit записан в `BUILD_COMMIT`, контрольные суммы — `MANIFEST.json`.

## Реализовано

- Один режим, 64 независимые песни на чистой grid 8×8. Клик pad переключает редактор, не играющую песню.
- Собственные имя, tempo, persistent pad/block colors, timeline, loop и delay.
- Полноширинный timeline; блок 44 вместо 66 px высотой, прежний горизонтальный масштаб (64 px/step, минимум 80 px для preset block). EMPTY компактнее; диапазоны динамические.
- PRESETS и WORK AREA по 260 px; UNO dark palette, custom scrollbar/buttons, тёмные dropdown/inputs.
- Только LOCAL/HARDWARE PRESETS. LOCAL: папки, выбор, drag/drop внешнего `.unosyp`. Правый клик браузера → Open folder меняет корень.
- Drop между блоками INSERT, внутри REPLACE с сохранением длины. Drag границы = RESIZE; возле стороны/тела = MOVE. Белые stippled полупрозрачные hover-стрелки. MOVE вправо создаёт EMPTY, влево сокращает/убирает его. Ripple сохранён.
- Лимит 64 steps каждой песни: отказ целиком с `64-step limit reached`.
- Click выбирает блок; Ctrl/Shift-click меняет multi-selection; пустое место снимает выделение. Shift-right-click задаёт loop от первого до последнего выделенного блока; повтор снимает тот же loop.
- Selection оранжевым border, playback белым индикатором, loop оранжевой линией. Основной цвет не заменяется.
- WORK AREA: NAME/TEMPO, DURATION/STEPS/BLOCKS, PLAY DELAY, текущая играющая песня/countdown и информация о выбранном блоке.
- Одна прямоугольная PLAY/STOP и Space вне Entry/Text. Старт с начала выбранного блока, иначе начала песни; active loop ограничивает старт/воспроизведение.
- Delay OFF/5/10/15/30/45/60 секунд с отменой. Переключение pad не меняет ожидающую запуска песню.

## Данные и совместимость

Один `LiveCreatorState.json` рядом с launcher. Автосохранение после изменения (300 ms debounce) и при закрытии; временный файл и атомарная замена.
Сохраняются 64 песни, global/controller settings, library root, имена, tempo, цвета, блоки, loop и delay. Transport/playhead после запуска не возобновляются.
References — абсолютные пути к оригиналам. Перенос библиотеки не переносит ссылки: отсутствующий файл показывает `PRESET NOT FOUND`; замените его drag/drop нужного файла.
Содержимое `.unosyp` не копируется, не преобразуется и не встраивается.
Повреждённый state не перезаписывается: ошибка загрузки отключает автосохранение до восстановления файла и перезапуска. Сделайте резервную копию перед ручным восстановлением.
`.unosong`, SONG PRESETS, NEW/OPEN/SAVE удалены; автоматического импорта старых `.unosong` нет. Исторические файлы/сборки не изменены.
Структурное редактирование останавливает transport редактируемой песни и сбрасывает её loop (унаследованное поведение); selection этого не делает.

## Заглушки и границы проверки

- Transport — software visual clock: один условный beat на Song Step. Нет звука, MIDI clock, применения UNO presets или полноценного sequencer playback.
- DURATION = steps × 60 / tempo, оценка условной модели, НЕ измеренная длительность hardware sequence. Loop может играть бесконечно.
- HARDWARE PRESETS: `UNO not connected`, чтение устройства не подключено.
- Controller settings зарезервированы; physical profiles/Launchpad/Note/CC mappings не реализованы. Дополнительного Controllers UI нет.
- SEND TO DEVICE, STORE/0x28, SEQ ON/OFF, COPY/PASTE не добавлялись.
- Системный выбор папки остаётся нативным диалогом; основные controls приложения тёмные.
- HARDWARE PASS не заявляется. Geometry assertions не заменяют визуальную приёмку на пользовательском экране/DPI.

## Software / regression

23 unittest: ripple-модель (9), библиотека/selection regression (3), session/state/transport (11).
Покрытие: insert/replace/resize/move, EMPTY/reverse, numbering, atomic overflow для каждой песни, старт блока, selection/playback, loop, cancel всех delays, независимая pending song, state roundtrip/invalid state, references без копий/missing preset.
Tk GUI smoke: drag/drop, resize, move/EMPTY, name, переключение pad, transport/delay cancel, missing preset; размеры 960×600, 1200×750, 1440×900, равные панели 260 px и pads внутри canvas.
Дополнительно: compile/import release-модулей, git diff --check, branch/scope review, ZIP CRC/SHA-256 manifest, отсутствие caches/runtime state.

## Изменённые файлы

- `core/session.py`, `core/state.py` — новые модели; `core/arrangement.py` — focus при снятии multi-selection.
- `ui/app.py` — единый редактор; `devices/uno/library.py` — references; старый `devices/uno/song.py` удалён (все пути внутри `live_creator`).
- `tests/test_session.py`, `tests/gui_smoke_v04.py` — новые проверки; `tests/test_v02.py` обновлён; `tests/test_v03.py` и `tests/gui_smoke_v02.py` удалены как отменённые container/GUI tests.
- `tests/build_live_creator.py` — упаковка v0.4-alpha.
- `AGENTS.md`, этот документ, итоговое ТЗ, `.gitignore` — текущая архитектура и исключение state/build outputs. Удалённый пользователем прежний task не восстанавливался.
