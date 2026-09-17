# UNO Pro Advanced — integration rules (2026-09-15)

Текущая версия основной линии: **v0.9.7-beta**, после v0.9.6-beta. Alpha-статус standalone Live Creator не переносится на основную программу. Прежнее обозначение v0.10.0-alpha было ошибочным локальным названием, не отдельным согласованным релизом. История сохраняется.
Текущая экспериментальная работа ведётся только в `test/v0.9.7-next`. `main` и `release/v0.9.7-beta` служат резервными точками и не изменяются без отдельной команды.
Актуальные документы релиза: `Docs/PROJECT_STATE.md`, `Docs/DECISIONS.md`, `Docs/RELEASE_NOTES_v0.9.7-beta.md` и `CHANGELOG.md`. Старые standalone build rules ниже относятся только к истории.
Общие документы `D:\UNO\docs\PROJECT_STATE.md` и `DECISIONS.md` синхронизируются с `Docs/PROJECT_STATE.md` и `Docs/DECISIONS.md` в репозитории для отправки на GitHub. Не повышать PARTIAL/UNKNOWN или hardware status при исправлении версии.

Документация является основой проекта и первичным источником истины. Недокументированное изменение не считается завершённым.
Новая анимация огибающей v0.9.7-beta и внутренняя геометрия отображаемой ADSR-кривой имеют статус **LOCKED / НЕ ИЗМЕНЯТЬ**. Без прямой отдельной команды пользователя запрещено менять S–R `0.26` (+30%), расчёты и отрисовку ADSR-кривой, Note On/Off, drag/edit, live-индикатор и код анимации. Контейнеры огибающей, положение блока на странице и окружающую компоновку SYNTH разрешено адаптировать, если сама ADSR-кривая и её анимация остаются неизменными.

Текущее ТЗ: `D:\UNO\UNO_LOCAL_INTEGRATION_TZ.md`, APPROVED FOR IMPLEMENTATION.
Пользователь явно разрешил интеграцию в `D:\UNO\project_unified`, ветка `main`, и финальную сборку после тестов, документации и commit. Это заменяет старые запреты ниже на изменение main.
Начальный main: `51906bc1a40a636441c98f10794113d696ffc180`; источник Live Creator: `e2b0a977d194fdf28e40eaac73b1eaae8de525b0`.
Сохранять MIDI/STORE/Fill. Native automation IDs/value/step и writer остаются PARTIAL/UNKNOWN. Темы централизованы; transport green/red не участвуют в accent swap. LENGTH ограничивает playback, но не удаляет позиции Timeline.

## Исторические standalone-правила (ограничение worktree отменено интеграционным ТЗ)

Работать только в `D:\UNO\Live-Creator`, ветка `live-creator`.
`D:\UNO\project_unified` и `main` не изменять.
Текущая standalone-версия: **v0.6-alpha**, review-итерация поверх v0.5-alpha. Упаковка разрешена отдельной командой пользователя «сделай сборку».
Перед работой читать `UNO_Local_Live_Creator_NEXT_ITERATION_TZ.md` и уточнения пользователя в текущем чате. Также доступны `UNO_Local_Live_Creator_NEXT_ITERATION_TZ_v2.md` и research handoff.
Не запускать упаковку до отдельной команды после визуальной приёмки. Отчёт текущей работы: `Docs/LIVE_CREATOR_REVIEW.md`.

## Согласованная модель

- Один режим. Grid 8×8 = 64 независимые песни, НЕ шаги одной песни.
- Каждая песня: timeline до 64 steps, имя, tempo, persistent pad/block colors, EMPTY, loop и delay.
- Editor selection, playing song, playhead и loop — отдельные состояния. Выбор другого pad не прерывает playback и не запускает другую песню.
- Один общий state: `%LOCALAPPDATA%\UnoLive\state\live_creator_state.json`. Общий root служебных данных UnoLive получается через environment, без имени пользователя в коде. В LOCAL PRESETS не создавать служебные файлы/папки.
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
Одна прямоугольная PLAY/STOP наверху WORK AREA, затем inline PLAY DELAY, цветной центрированный NAME, узкий TEMPO непосредственно рядом с label, DURATION/ELAPSED/REMAINING/STEPS/BLOCKS/MARKERS. Нет постоянной палитры, COLOR button, block-info и STATUS/READY. Ошибки показываются только при ошибке. Space/Delete/Ctrl+X/C/V не перехватываются в текстовых полях.
Одна общая тёмная popup-палитра вызывается через Color... в обоих объектных меню. Song color и block color независимы.
Delete и Right Click → Delete удаляют выбранные blocks с ripple; постоянной кнопки нет.
Empty pad показывает только номер; filled — только word-wrapped/ellipsis song name. Playing pad/block слегка светлее с мягкой пульсацией; selection border сохраняется. Moving playhead отсутствует.
Старт с начала выбранного блока, иначе начала песни. Назначенный Loop не переносит позицию. При достижении он становится ACTIVE. PLAY внутри ACTIVE = exit loop + continue, а не STOP.
Delay OFF/5/10/15/30/45/60 секунд, повторный PLAY/Space отменяет countdown.

## Архитектура и безопасность

Сохранять `core / ui / controllers / devices`. Generic core не зависит от UNO, `.unosyp` или конкретного controller.
`core/session.py` — 64 песни и независимый transport context. `core/state.py` — единый JSON, атомарная запись; повреждённый state не перезаписывать автоматически.
Editor song и playback snapshot разделены, как и selected blocks / playing block ID. Изменения редактора применяются при следующем запуске; текущий snapshot не мутируется выбором или редактированием. Transport: STOPPED / COUNTDOWN / PLAYING; Loop: NONE / ASSIGNED / ACTIVE.
Playback пока software, без MIDI и звука, но timing считается по музыкальной длине: подтверждённые raw offsets 207–208, `value=data[207] | data[208]<<7`, `length=(value+1)//8`; пользователь подтвердил шаг = 1/16. Seconds = length / 4 × repeats × 60 / BPM. Никакого fallback 1 beat/Song Step или удержания последнего блока. Завершение по номинальному времени; Loop не входит в DURATION, elapsed отражает позицию структуры.
Для неподдерживаемого/повреждённого файла и пока не согласованной музыкальной длительности EMPTY — неизвестное время, без выдуманного playback.
Markers — отдельная карта начал секций по Song Step, не поле блока. При ripple следуют структурной позиции; при удалении переносятся на следующий блок. Конфликт двух разных markers на одной позиции — known issue: операция отклоняется атомарно, без объединения через '/' и без потери подписей.
Внутренний clipboard копирует блоки с reference/length/color/parameters, но без markers. Song copy сохраняет песню, включая markers, без копирования/удаления файлов presets.
HARDWARE PRESETS — заглушка. Physical profiles не подключены. SEND TO DEVICE не добавлять.
Не выдумывать MIDI/SysEx/Note/CC. STORE/0x28 locked; SEQ ON/OFF без mapping не трогать.
`IMPLEMENTED`, `SOFTWARE PASS`, `HARDWARE PASS` различать. Hardware pass только после проверки реального железа.

## Проверки и сборка

Сборка только по явному запросу. Текущий workflow — standalone **source release** для Python 3.10+ с Tkinter, не автономный EXE.
Перед упаковкой: compile/import, unittest regression, Tk GUI smoke, git diff --check, проверка ветки и состава изменений.
`tests/build_live_creator.py` собирает versioned directory + ZIP в `builds`, проверяет CRC/SHA-256 manifest и записывает BUILD_COMMIT.
Не включать пользовательский state, presets, caches или временные captures. Исторические сборки не менять.
Для текущего review запускать `tests/gui_smoke_review.py` и unittest discovery. `tests/review_preview.py` — изолированные синтетические визуальные fixtures, не пользовательский state и не сборка. Тестовый state имеет явный override пути и находится вне fixtures-библиотеки.
Актуальный release report: `Docs/LIVE_CREATOR_v0.6-alpha.md`. Builder упаковывает v0.6-alpha и отклоняет перезапись существующего каталога/ZIP. Исторические сборки не перезаписывать.
