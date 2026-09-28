# Changelog

## v0.9.7-beta2 VISUAL-FIX-GET-SEND — 2026-09-25

- База сборки: `UNO2.2_VISUAL_FIX`; существующая графика не перерабатывалась.
- LIVE перед каждым клипом выбирает принадлежащий ему hardware-пресет либо загружает локальный `.unosyp` в текущий буфер командой `0x36`.
- `STORE` оставлен только на странице SYNTH и пишет текущий редакторский буфер.
- В панели Hardware библиотеки добавлены `GET` и `SEND`.
- `GET` вручную опрашивает имена всех 256 слотов с быстрым 5 ms конвейером, повторяет только пропущенные ответы, показывает ход и атомарно обновляет кеш. Автоматический полный опрос при запуске удалён.
- LOCAL → Hardware и перестановка Hardware → Hardware теперь изменяют только сохранённый план банка приложения.
- `SEND` пишет выделенные подготовленные слоты. Для переставляемого пресета, который существует только в UNO, сначала читается полное состояние и секвенция во временный кеш, затем запускается writer.
- Слоты 1–128 не считаются неизменяемыми заводскими: GET всегда принимает фактические имена устройства.

- Library layout: restored right borders on both preset containers, fixed LOCAL
  to three preset columns and assigned the remaining width to the right panel.
- Removed duplicate STORE and RECEIVE controls from the Library panel; STORE
  remains available in the main application toolbar.
- Reduced the Library page header height and enlarged anti-aliased tag circles
  consistently in the filter strip and tag selection menus.
- Fixed factory multi-step Step Automation decoding: cumulative page value
  prefixes are no longer rejected as mismatched mirrors, and the validated
  CUTOFF1 lane from `FAKE 808(1).unosyp` is loaded into the sequencer editor.

## 0.9.7-beta2 STORE Library simple — 2026-09-22

- Удалена дублирующая кнопка Send из панели аппаратной библиотеки.
- STORE остаётся единственной кнопкой записи в выбранный слот UNO; Receive сохраняет текущий аппаратный буфер локально.
- Прямая передача перетаскиваемого локального бинарного файла сохранена.

## 0.9.7-beta2 STORE local source — 2026-09-22

- Перетаскивание локального бинарного `.unosyp` на аппаратный слот теперь использует состояние и четыре страницы самого файла, а не ранее загруженный edit buffer.
- Локальные записи без полного бинарного исходника отклоняются до начала STORE.
- Верхняя кнопка STORE и STORE на панели UNO по-прежнему сохраняют текущий edit buffer.
- `uno_step_automation_decoder.py` остаётся в исходниках как структурный и ограниченный точными capture профилями читатель; универсальное чтение дорожек автоматизации не заявляется.
- Протокол и последовательность STORE не менялись; новый путь передачи файла требует проверки на тестовом аппаратном слоте.

## 0.9.7-beta2 STORE Library decoder — 2026-09-22

- Read-only decoder интегрирован в обработку переменно-размерных `.unosyp`.
- Точное распознавание 13 capture-профилей; неподтверждённые наборы остаются PARTIAL с raw payload.
- ENV1, ENV2 и SPACING в подтверждённых профилях читаются как signed 8-bit.
- Старый фиксированный формат и аппаратная транзакция STORE сохранены без изменений.
- SOFTWARE PASS для двух новых проверок интеграции и 16 предоставленных capture.

## 0.9.7-beta2 STORE Library panel — 2026-09-22

- В панели UNO библиотеки добавлена кнопка STORE для выделенного аппаратного слота.
- Кнопка Send использует тот же выбранный слот; подтверждение показывает номер и имя перед перезаписью.
- При перетаскивании на аппаратный слот больше не вызывается Program Change перед STORE, чтобы сохранить текущий edit buffer.
- Принятая транзакция STORE 0x11/0x23/0x28/0x33, чтение 0x29/0x37 и адресация банков не менялись.
- Программно проверен выбор слота и отсутствие загрузки целевого пресета до STORE. Аппаратную проверку новой точки входа необходимо провести отдельно.

## 0.9.7-beta — 2026-09-17

- Объединён декодер секвенсора локальных `.unosyp` и аппаратных страниц SysEx `0x29`.
- Добавлено подтверждённое декодирование Gate, Accent и TIE в обеих ветвях загрузки.
- Аппаратный приём расширен до страниц 0–4 для полного чтения секвенсора.
- Применён патч анимации огибающей.
- Визуальный отрезок S–R огибающей увеличен на 30%.
- Новая огибающая и код её анимации зафиксированы как `LOCKED / НЕ ИЗМЕНЯТЬ` без прямого указания пользователя.
- Версия интерфейса и `VERSION` обновлены до 0.9.7-beta.

## 0.9.6-beta

- Интегрирован Live Creator в основную beta-линию UNO Pro Advanced.
## 0.9.7-beta2-CANONICAL-STEP-DECODER — 2026-09-23

- Один канонический Step Automation decoder для заводских `.unosyp` и hardware `0x29`.
- Добавлен аппаратный предел 18 automation parameters на шаг.
- Поддержаны подтверждённые SINGLE, adjacent pair, GAP, MASTER/MASTER_7 и SET profiles.
- Неизвестные и неоднозначные signatures сохраняются RAW без выдуманного parameter ID.
- UI, STORE, preset writer и hardware write path не изменялись.
## 0.9.7-beta2-HARDWARE-AUTOMATION-FIX — 2026-09-23

- Исправлен перенос декодированной Step Automation из hardware `0x29` в дорожки Sequence.
- Заводской `[053] FAKE 808` показывает восемь точек `CUTOFF 1` на шагах 6, 7, 11, 23, 27, 54, 55 и 59.
- Добавлен обязательный regression test полного аппаратного пути на `FAKE 808`.
- UI не изменялся.
## MPC-PADS edit — hardware catalog and persistent LIVE clips — 2026-09-24

- Графика, геометрия и отрисовка не изменялись.
- Имена аппаратных пресетов 1–256 сохраняются в `%LOCALAPPDATA%\UnoLive\hardware_preset_names.json` и отображаются сразу при следующем запуске.
- Последовательный опрос с ожиданием каждого слота заменён фоновым конвейером запросов и одним повторным проходом только по слотам без ответа; перерисовка списка ограничена по частоте.
- Заводские hardware-клипы LIVE сохраняют пять прочитанных страниц в данных блока песни и восстанавливаются после перезапуска без локального `.unosyp`; writer в этом пути не участвует.
- Существующие STORE, decoder и guarded native writer сохранены.
- Hardware catalog больше не перегружает MIDI вход запросами через 6 ms: первый проход выполняется с безопасным интервалом 30 ms, пропущенные ответы повторяются до трёх раз с интервалом 70 ms.
- Исправлено отсечение последней колонки hardware library: слоты 241–256, включая пустые, теперь всегда доступны при прокрутке.
- STORE локального пресета больше не перерисовывает всё окно на каждом этапе SysEx handshake.
- Добавлена пакетная загрузка: перетаскивание локальной папки на hardware slot предварительно проверяет все `.unosyp` и записывает их последовательно, начиная с выбранного слота, с одним подтверждением диапазона.
- Исправлена обратная кнопка `< Move`: выбранный hardware-пресет читается через `0x37` и страницы `0x29`, собирается в native binary `.unosyp` и сохраняется в выбранную папку LOCAL. Hardware slot больше ошибочно не используется как локальная цель.
- Исправлен viewport Hardware Library: частично видимые колонки больше не рисуются поверх LOCAL-панели, а увеличенный конечный ход scrollbar по-прежнему позволяет полностью показать слоты 241–256.
- В обеих панелях Library добавлено пакетное выделение: `Ctrl` добавляет или убирает отдельные пресеты, `Shift` выделяет непрерывный диапазон от опорного элемента, `Ctrl+Shift` добавляет диапазон.
- Кнопки `Move >` и `< Move` обрабатывают пакетное выделение: локальные файлы записываются с выбранного стартового слота либо в равное число выбранных слотов, а hardware-пресеты последовательно сохраняются в выбранную LOCAL-папку.
- Hardware Library при запуске немедленно загружается из локального снимка, а после подключения UNO проверяет 256 слотов в фоне. Снимок версии 2 хранит имена, подтверждённые и не ответившие слоты, время начала и завершения проверки; пропущенный MIDI-ответ не удаляет ранее сохранённое имя.
- Завершённый `STORE` сразу обновляет имя соответствующего hardware-слота в том же снимке; LIVE и основная Library используют общий кеш без потери метаданных проверки.
- Исправлен LIVE playback: перед воспроизведением последовательности каждого блока UNO получает принадлежащий блоку звук — hardware-клип выбирает свой Bank/Program, локальный binary `.unosyp` загружается во временный edit buffer командой `0x36`. Текущий пресет главного окна больше не используется как звук всех клипов.
- Исправлена команда `STORE` на странице Library: выделенный hardware-слот является источником выбора на физическом UNO. Команда больше не записывает текущий edit buffer главного окна в выделенный слот; запись локальных файлов остаётся за `Move >`.

## 2026-09-25 — LIVE MIDI Controller
- Added independent LIVE MIDI IN/OUT/channel settings.
- Added Launchpad X Programmer 8x8 mapping (Note 11–88).
- Added Custom MIDI Learn for SONG 01–64, PLAY and STOP actions.
- PLAY arms LIVE pad switching; pads can launch songs during LIVE playback.
- Added controller LED/transport feedback over LIVE MIDI OUT.
- UNO MIDI and SEQUENCER paths are unchanged.

## 2026-09-25 — LIVE clip/PLAY state fix
- Clip selection no longer changes the visual active state of the LIVE PLAY transport button.
- PLAY active indication is now tied to an explicit playback start and is cleared on stop/end.
- No sequencer or MIDI mapping changes.

## 2026-09-25 — LIVE STOP mode fix
- STOP now explicitly clears LIVE performance mode.
- After STOP, pad/clip clicks return to normal selection/editing instead of launching playback.
- PLAY continues to enable LIVE performance mode.
