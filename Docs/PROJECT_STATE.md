# UNO Pro Advanced — состояние проекта

## VISUAL-FIX GET/SEND (2026-09-25)

- Рабочая база и визуальный контракт: `UNO2.2_VISUAL_FIX`.
- Hardware catalog хранится в `%LOCALAPPDATA%\UnoLive\hardware_preset_names.json` и при запуске читается без автоматического MIDI-опроса.
- Ручной `GET` является единственным владельцем полного обновления списка устройства.
- План Hardware банка хранится отдельно в `%LOCALAPPDATA%\UnoLive\hardware_bank_stage.json`.
- Перемещения в панели Hardware являются staging-операциями. Запись на UNO выполняется только `SEND` для выделенных слотов.
- Полные device-only источники, необходимые для перестановки, перед записью сохраняются в `%LOCALAPPDATA%\UnoLive\hardware_presets`.
- `STORE` применяется только на SYNTH к текущему редакторскому буферу.
- LIVE playback явно загружает пресет текущего клипа перед воспроизведением его секвенции.

## MPC-PADS edit: каталог hardware и factory clips в LIVE

- Рабочая база: `UNO_Pro_Advanced_v0.9.7-beta2-MPC-PADS_edit.rar`.
- Визуальная часть зафиксирована и этой работой не изменяется.
- Hardware catalog использует постоянный локальный кэш имён и быстрый фоновый опрос 1–256 с повтором только пропущенных ответов.
- Опрос имён ограничен безопасной для UNO скоростью: 30 ms между первичными запросами и до трёх повторов пропущенных ответов по 70 ms. Последняя колонка hardware library не отсекается viewport-проверкой.
- Локальную папку `.unosyp` можно перетащить на hardware slot для последовательной загрузки банка; все файлы проверяются до первой записи, диапазон подтверждается один раз.
- Направления кнопок Library зафиксированы: `Move >` пишет выбранный LOCAL preset в выбранный hardware slot; `< Move` читает выбранный hardware slot и сохраняет native binary `.unosyp` в текущую выбранную LOCAL-папку.
- Заводской hardware-клип LIVE хранит read-only snapshot пяти аппаратных страниц в `PresetBlock.parameters`. Writer для этого не используется; клип восстанавливается после перезапуска без локального `.unosyp`.
- STORE и decoder присутствуют. Writer остаётся guarded/partial: значения уже распознанных native targets записываются, синтез нового Selection/Control не заявляется.

Дата фиксации: 2026-09-17.

## Основное правило ведения проекта

Документация является основой проекта и первичным источником истины. Исследования, подтверждённые структуры и алгоритмы, решения, ограничения и результаты тестов фиксируются до выпуска сборки или одновременно с изменением кода. Недокументированное изменение не считается завершённым. При расхождении источников продолжение работы выполняется по актуальной документации с явным сохранением статусов подтверждения.

## Защищённый компонент: анимация и геометрия ADSR

Статус: **LOCKED / НЕ ИЗМЕНЯТЬ**.

Новая анимация огибающей v0.9.7-beta и внутренняя геометрия отображаемой ADSR-кривой защищены запретом на изменения без отдельного указания пользователя. Зафиксированы S–R `0.26` (+30%), расчёты координат/времени/уровня, кривые, отрисовка, маркеры, live-индикатор, Note On/Note Off и drag/edit-поведение. Контейнеры FILTER ENV/AMP ENV, положение всего блока и окружающую компоновку SYNTH разрешено адаптировать при неизменной ADSR-кривой и анимации.

## Актуальная линия

- Основной проект: `D:\UNO\project_unified`, ветка `main`.
- Текущая версия: **v0.9.7-beta**, кумулятивно после v0.9.6-beta.
- База main: `51906bc1a40a636441c98f10794113d696ffc180`; Live Creator: `e2b0a977d194fdf28e40eaac73b1eaae8de525b0`.
- Интеграционный merge: `2a63c2684c89881003bdd015cc24a58dbde11e95`. Его прежнее название v0.10.0-alpha было ошибочным и исправляется отдельным commit без переписывания истории.
- Версия standalone Live Creator v0.6-alpha не меняет beta-статус основной программы.
- Отдельный worktree Live-Creator и его пользовательские материалы не изменяются.

## Тестовая линия адаптивного UI

- Активная ветка разработки: `test/v0.9.7-next`, база — зафиксированный релиз v0.9.7-beta.
- `main` и `release/v0.9.7-beta` являются резервными точками и в рамках UI-эксперимента не изменяются.
- Реализуется поэтапный responsive layout без боковых полей на стандартных 16:9 экранах. Контрольные размеры: 1366×768, 1600×900, 1920×1080, 2560×1440.
- Этап 1: добавлен чистый расчёт viewport и гибких колонок; адаптируются topbar, SYNTH, Sequencer, Library, Settings, Live Creator и экранная клавиатура.
- SYNTH использует три пропорционально расширяемые зоны: OSC, FILTER/LFO/ENV и FX. Мод-матрица расширяется по доступной ширине. ADSR-графики сохраняют исходные размеры, внутреннюю геометрию и анимацию; перемещаются только их контейнеры и положение на странице.
- Добавлены unit-проверки layout-математики и исходного кода защищённых функций огибающей.
- Layout unit-тесты на четырёх стандартных разрешениях, адаптивные зоны SYNTH и lock-тест огибающей: **SOFTWARE PASS**. Полная регрессия: 61/63 PASS; остаются два ранее документированных устаревших ожидания `test_safety_unchanged` и `test_theme`, не связанные с UI-изменением. Визуальная проверка реального Tk-окна: **UNVERIFIED** из-за отсутствия display/Xvfb в среде.
- Пользователь разрешил тестовую сборку. Целевой артефакт: `UNO_Pro_Advanced_v0.9.7-next.zip`, канал `test/v0.9.7-next`; `VERSION` приложения остаётся `0.9.7-beta`.
- Тестовая сборка проверена пользователем: адаптивная компоновка получила **USER VISUAL PASS**.
- Пользователь разрешил fast-forward перенос тестовой линии в `main` и закрытие `test/v0.9.7-next`. После интеграции актуальной рабочей веткой снова является `main`; `release/v0.9.7-beta` сохраняется как резервная точка.

## Реализовано в интеграции

Встроенный LIVE: 64 независимые песни, Timeline 32+32, LENGTH 1–64 без удаления блоков, скругление 4px, независимый выбранный и проигрываемый контекст, clipboard/markers/Loop/pulse.
Sequencer: Dupl с удвоением длины и копированием декодированной automation, прежний Fill.
Automation: parameter selector, индивидуальная metadata шкал и read-only native container reader.
Dark/Light темы, неизменные transport green/red, Settings/Theme icons. Служебные данные — `%LOCALAPPDATA%\UnoLive`, не LOCAL PRESETS.

## Изменения v0.9.7-beta

- Локальные `.unosyp` и аппаратные страницы SysEx `0x29` используют общий декодер секвенсора.
- Gate, Accent и TIE полностью декодируются и переносятся в одну модель `Step` независимо от источника данных.
- Аппаратный приём собирает страницы 0–4, необходимые для подтверждённого декодирования секвенсора.
- Добавлена новая анимация огибающей; визуальный отрезок S–R увеличен на 30%. Компонент после утверждения переведён в статус LOCKED.
- Название окна, экран About и файл `VERSION` синхронизированы с **0.9.7-beta**.

## Проверки и границы подтверждения

57 актуальных unittest повторно прошли при исправлении версии; compile/import и version-only runtime diff также PASS. Два Tk GUI smoke-теста и packaged main проходили до переименования, но повторная проверка beta заблокирована отсутствием прежней Tcl/Tk-папки и отклонённым доступом к установленному Python. Новый GUI/launch PASS не заявляется; требуется повторная проверка после восстановления среды. При автоматическом запуске используется mocked MIDI и временное хранилище.
На предоставленных файлах из `D:\UNO\materials\test` проверены 6 automation containers и 12 Sequence Length. Это SOFTWARE validation реальных captures, не новое аппаратное испытание.
Единый декодер Gate/Accent/TIE проверен на 10 контрольных `.unosyp`: результаты локального чтения и эквивалентного аппаратного payload совпадают. Это SOFTWARE PASS на подтверждённых captures; физический обмен с устройством в рамках этой сборки не выполнялся.
Проверка репозитория перед GitHub push: compileall PASS, `git diff --check` PASS, версия/огибающая/документная блокировка PASS, parity Gate/Accent/TIE на 10 captures PASS. Из 57 исторических unittest прошли 55; два старых теста конфликтуют с утверждёнными изменениями v0.9.7-beta: `test_safety_unchanged` запрещает обновление `hardware_seq_0x29.py`, а `test_theme` ожидает прежний Light accent swap. Код под эти устаревшие ожидания не откатывался.
Исторические аппаратные результаты основной beta-линии не являются HARDWARE PASS новой интеграционной сборки.
Старый Docs/test_beta.py содержит несовместимые проверки отсутствующих в исходной базе API и старого SONG UI; подробности в отчёте.
Финальный ручной visual PASS не получен из-за ограничения инструмента.

## PARTIAL / UNKNOWN / UNVERIFIED

- Native automation: parameter/value/step packing и writer PARTIAL; byte495 и аппаратный MAX entries UNKNOWN. Не устанавливать MAX=17.
- Dupl блокируется при opaque native automation, чтобы не терять события.
- Tune hybrid, Wave normalization, mode-aware LFO и raw CC → device-unit conversion не дополняются догадками.
- Live playback без MIDI/звука/controllers/hardware SONG writes.
- Музыкальная длительность EMPTY неизвестна; конфликт markers отменяет edit без объединения через /.
- Исторический статус 2026-09-17: STORE/0x28 locked; неизвестный SEQ ON/OFF не изменён.
- Обновление 2026-09-22: принята аппаратно проверенная база STORE-SEQUENTIAL-FIX (последовательность 0x11/0x23/0x28/0x33 и адресация слотов). В панели LIBRARY добавлена точка входа STORE для выделенного аппаратного слота, её аппаратная проверка пока не выполнена. См. `Docs/STORE_LIBRARY_PANEL_2026-09-22.md`.
- Выборочные исторические ограничения hardware 0x29 не считаются закрытыми этой интеграцией.

## Сборка и отправка

Актуальный артефакт: `UNO_Pro_Advanced_v0.9.7-beta.zip`.
Source standalone для Python 3.12+, Tkinter, Pillow, не автономный EXE. Source hash — BUILD_COMMIT внутри архива.
Старую локальную v0.10.0-alpha не публиковать; она сохранена как superseded artifact.
Push/создание тегов/публикация GitHub Release пока не выполняются. Remote main не удалось проверить из-за отсутствия соединения с GitHub; перед push повторить fetch и ancestry check, не использовать force push.

## Рабочая сборка 2026-09-23 — canonical Step Automation decoder

- По прямой команде пользователя разрешена source-сборка текущего рабочего snapshot.
- Имя артефакта: `UNO_Pro_Advanced_v0.9.7-beta2-CANONICAL-STEP-DECODER.zip`.
- Заводские `.unosyp` и аппаратные страницы `0x29` используют один канонический read-only декодер Step Automation.
- Подтверждённый аппаратный предел — не более 18 automation entries на шаг.
- Неоднозначные/неизвестные комбинации сохраняются RAW и не получают выдуманный parameter ID.
- UI, preset writer, STORE и hardware write path этой работой не изменялись.
- Статус: SOFTWARE PASS для контролируемого корпуса; HARDWARE PASS не заявляется.
- Рабочая копия не содержит `.git`, поэтому `BUILD_COMMIT` пакета фиксируется как `workspace-snapshot-2026-09-23`, без ложной ссылки на Git commit.

## Исправленная сборка 2026-09-23 — hardware automation integration

- Предыдущий `CANONICAL-STEP-DECODER` признан дефектным: hardware adapter декодировал Step Automation, но не переносил её в `Sequence.automation`.
- Исправление переносит результаты единого декодера из страниц `0x29` в соответствующие дорожки редактора.
- Заводской `[053] FAKE 808` подтверждён через полный hardware path: `CUTOFF 1`, шаги 6, 7, 11, 23, 27, 54, 55, 59; первые значения 511, 512, 511.
- Новый артефакт: `UNO_Pro_Advanced_v0.9.7-beta2-HARDWARE-AUTOMATION-FIX.zip`.
- UI не изменялся; HARDWARE PASS на физическом устройстве не заявляется.

## Документация

Для v0.9.7-beta актуальны `Docs/RELEASE_NOTES_v0.9.7-beta.md`, `Docs/PROJECT_STATE.md`, `Docs/DECISIONS.md` и `CHANGELOG.md`.
Этот файл и DECISIONS.md зеркалируются из `D:\UNO\docs` в `D:\UNO\project_unified\Docs`, чтобы общие решения были доступны и на GitHub.

## Рабочая сборка 2026-09-25 — SEQUENCER redesign

- Артефакт: `UNO_Pro_Advanced_v0.9.7-beta2-SEQUENCER-REDESIGN.zip`.
- Формат: source snapshot; рабочая копия не содержит `.git`, поэтому BUILD_COMMIT фиксирует workspace source ID, а не Git commit.
- SEQUENCER: новый layout, piano-roll group editing/zoom, collapsible Automation + VELOCITY, global Gate/Accent decode/model/UI/native write.
- Per-note `Extra` остаётся UNKNOWN и не используется как Length/Aftertouch writer mapping.
- Проверка: compile PASS; focused sequencer/automation pytest PASS (12 passed, 4 skipped, 4 subtests). Полный suite: 90 passed, 4 skipped, 19 subtests, 4 legacy failures; один требует отсутствующий Git repository, остальные относятся к прежним theme/live-creator tests. GUI smoke не выполнен: display недоступен.
