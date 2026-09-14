# Live Creator — актуальные правила

Работать только в `D:\UNO\Live-Creator`, ветка `live-creator`.
`D:\UNO\project_unified` и `main` не изменять.
Текущая standalone-версия: **v0.5-alpha**.
Перед работой целиком читать `UNO_Local_Live_Creator_NEXT_ITERATION_TASK.md`.
Это ТЗ заменяет конфликтующие пункты предыдущего задания. Документы v0.1–v0.4 и старые сборки — история, не актуальная архитектура.

## Согласованная модель

- Один режим. Grid 8×8 = 64 независимые песни, НЕ шаги одной песни.
- Каждая песня: timeline до 64 steps, имя, tempo, persistent pad/block colors, EMPTY, loop и delay.
- Editor selection, playing song, playhead и loop — отдельные состояния. Выбор другого pad не прерывает playback и не запускает другую песню.
- Один `LiveCreatorState.json` рядом с launcher: все песни, global settings и controller settings.
- Только ссылки на оригинальные `.unosyp`, никаких embedded/скрытых копий. Отсутствующий файл: `PRESET NOT FOUND`.
- Не возвращать `.unosong`, SONG PRESETS, NEW/OPEN/SAVE, CREATOR/LIVE и внешние ряды Launchpad.

## Геометрия и управление

Timeline — фиксированные строки 01–32 и 33–64 без горизонтального scroll. Одинаковая slot width в обеих строках адаптируется к ширине окна. EMPTY занимает точное число slots. Блок через 32/33 рисуется двумя сегментами с одним ID.
PRESETS и WORK AREA — по 260 px; чистая 8×8 grid в центре.
UNO palette, тёмные inputs/dropdown, custom scrollbar/buttons; без дополнительных декоративных контролов.
DROP между блоками = INSERT, внутрь = REPLACE с сохранением длины.
MOVE/RESIZE — drag; white hover arrows удалены. Только настоящая граница логического блока = resize. Drag preset имеет ghost и snap preview INSERT/REPLACE.
Ripple с EMPTY; превышение 64 отклонять целиком, не обрезать.
Multi-selection: Ctrl/Shift-click. Shift-right-click задаёт/снимает loop по выделению.
Одна прямоугольная PLAY/STOP наверху WORK AREA, затем inline PLAY DELAY, NAME над широким input, inline узкий TEMPO, метрики и persistent color palette. Block-info и постоянного STATUS/READY нет. Ошибки показываются только при ошибке. Space и Delete не перехватываются в текстовых полях.
Delete и Right Click → Delete удаляют выбранные blocks с ripple; постоянной кнопки нет.
Empty pad показывает только номер; filled — только word-wrapped/ellipsis song name. Playing pad/block слегка светлее с мягкой пульсацией; selection border сохраняется. Moving playhead отсутствует.
Старт с начала выбранного блока, иначе начала песни; active loop ограничивает диапазон.
Delay OFF/5/10/15/30/45/60 секунд, повторный PLAY/Space отменяет countdown.

## Архитектура и безопасность

Сохранять `core / ui / controllers / devices`. Generic core не зависит от UNO, `.unosyp` или конкретного controller.
`core/session.py` — 64 песни и независимый transport context. `core/state.py` — единый JSON, атомарная запись; повреждённый state не перезаписывать автоматически.
Редактирование структуры играющей песни останавливает её software transport и сбрасывает loop — унаследованное правило. Selection этого не делает.
Playback пока визуальный: один условный beat на Song Step. Достижение последнего блока удерживает visual transport до явного STOP; автоматическое завершение короткой песни больше не сбрасывает кнопку через полсекунды. Это не аппаратное playback и не искусственный timeout кнопки. DURATION — прежняя условная оценка, не длительность UNO sequence. Active loop продолжает цикл.
HARDWARE PRESETS — заглушка. Physical profiles не подключены. SEND TO DEVICE не добавлять.
Не выдумывать MIDI/SysEx/Note/CC. STORE/0x28 locked; SEQ ON/OFF без mapping не трогать.
`IMPLEMENTED`, `SOFTWARE PASS`, `HARDWARE PASS` различать. Hardware pass только после проверки реального железа.

## Проверки и сборка

Сборка только по явному запросу. Текущий workflow — standalone **source release** для Python 3.10+ с Tkinter, не автономный EXE.
Перед упаковкой: compile/import, unittest regression, Tk GUI smoke, git diff --check, проверка ветки и состава изменений.
`tests/build_live_creator.py` собирает versioned directory + ZIP в `builds`, проверяет CRC/SHA-256 manifest и записывает BUILD_COMMIT.
Не включать пользовательский state, presets, caches или временные captures. Исторические сборки не менять.
Обновлять документацию каждого релиза: `Docs/LIVE_CREATOR_v0.5-alpha.md`.
