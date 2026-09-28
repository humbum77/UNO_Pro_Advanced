# Live Creator v0.5-alpha — отчёт следующей итерации

## Запуск и границы

ТЗ: `UNO_Local_Live_Creator_NEXT_ITERATION_TASK.md`, заменяет конфликтующие пункты предыдущего задания.
Работа: только `D:\UNO\Live-Creator`, ветка `live-creator`. Основной проект и main не изменяются.
Standalone source release для Python 3.10+ с Tkinter, не автономный EXE. Запуск `run_live_creator.bat` или `python -m live_creator`.
Папка: `D:\UNO\Live-Creator\builds\Live_Creator_v0.5-alpha`.
Архив: `D:\UNO\Live-Creator\builds\Live_Creator_v0.5-alpha.zip`.
Commit сборки: см. `BUILD_COMMIT` внутри папки/ZIP; SHA-256 файлов: `MANIFEST.json`.

## PLAY: фактическая причина и исправление

В v0.4 `Session.update` вызывал `Arrangement.advance`, затем `Session.stop` по окончании условной beat-шкалы. Песня из одного шага при 120 BPM завершалась за 0.5 s. Поэтому STOP быстро возвращался в PLAY без второго клика. Это воспроизводится на синтетическом времени; аппаратный capture не требуется.
В v0.5 окончание условной шкалы и явный STOP разделены: visual audition удерживает последний блок и остаётся активным до STOP. Следующий beat больше не планируется; нет искусственной задержки кнопки и автоматического loop. Active loop продолжает работать. Кнопка и пульсация используют состояние одной Session.
Пустая песня по-прежнему не запускается. Структурное редактирование играющей песни по-прежнему останавливает transport/сбрасывает loop, selection — нет.
Это ограниченный visual transport, не полноценное аудио/UNO playback. Точное аппаратное время неизвестно. DURATION пока прежняя оценка steps × 60 / BPM, не длительность реальных sequences.

## Acceptance checklist

Статус ниже — IMPLEMENTED / SOFTWARE PASS; визуальная приёмка на пользовательском экране отдельно. Ни один пункт не означает HARDWARE PASS.

| № | Требование | Реализация / проверка |
|---|---|---|
| 1 | 01–32 и 33–64 одновременно | Две строки, 64 slot labels; Tk smoke |
| 2 | 32 равных slots помещаются | Общая Slots geometry; 960/1200/1440 px окна |
| 3 | Точная геометрия EMPTY | Та же pitch, что preset; assertions длины |
| 4 | Блок через 32/33 остаётся одним | Один ID, два сегмента, общие selection/resize/delete |
| 5 | Тонкая grid | 66 линий, усиление через 8 slots |
| 6 | Компактность и имя | Блок 30 px вместо 44; pixel-measured ellipsis |
| 7 | Нет moving playhead | Линия playhead удалена; текущий step только внутренний |
| 8 | Playing block пульсирует | Общая мягкая трёхсекундная brightness-функция |
| 9 | Нет white MOVE arrows | Удалены |
| 10 | Drag/resize/ripple/EMPTY | Model regression + GUI drag туда/обратно и resize двухстрочного блока |
| 11 | DEL/context Delete | Multi-delete core, text-focus guard, context action GUI test |
| 12 | Отдельная LOCAL-нумерация | Колонка 001… только для preset rows, не часть имени |
| 13 | Ghost/target | Floating ghost и slot overlay во время drag |
| 14 | INSERT/REPLACE preview | Текст операции; insert boundary line; общий target для preview/drop |
| 15 | Квадратные pads | Одна size для обеих сторон; fit assertions |
| 16 | Empty pad: номер | Единственная надпись 01…64 |
| 17 | Filled pad: имя | Номер не создаётся |
| 18 | Перенос имени | По словам; измерение шрифта и ellipsis по доступным строкам |
| 19 | Persistent color | Палитра WORK AREA; state/restart test |
| 20 | Playing pad ярче/pulse | Та же функция, что timeline; после STOP исходный цвет |
| 21 | Selected+Playing | Оранжевый border не заменяется яркостью фона |
| 22 | Нет block-info | Секция и переменная удалены |
| 23 | PLAY наверху | Проверка порядка координат |
| 24 | Inline PLAY DELAY | Label/dropdown внутри одной строки |
| 25 | NAME | Label над input по ширине панели |
| 26 | TEMPO | Inline label и Entry width=3 |
| 27 | Нет STATUS/READY | Постоянная секция удалена; только условная ошибка, countdown на STOP |
| 28 | Нет быстрого возврата PLAY | Lifecycle regression 0.01/0.5/1/100 s; ручной STOP |
| 29 | Space | GUI test transport/countdown и text-focus guard |
| 30 | Pad selection не останавливает | Независимый playing_pad, regression/GUI |
| 31 | Общий state | Прежний JSON v1 совместим, roundtrip/restart |
| 32 | main не затронут | Scope review и неизменный main ref |
| 33 | Нет выдуманных MIDI | Нет отправки hardware-команд; static review |

## Проверки

- 30 unittest: прежние ripple/reference/session/state regressions + Slots/boundary, delete, atomic gap-drop, pulse, transport lifecycle и включение loop после удержания последнего блока.
- Tk GUI smoke: 32+32, split block, resize/move reverse, exact EMPTY, selection, preview modes/ghost, numbering, DEL/context action, PLAY/Space/delay, color/state restart, layout на трёх размерах.
- Compile/import release modules; git diff --check; проверка состава изменений.
- ZIP CRC/SHA-256 manifest, отсутствие `.unosyp`, `.unosong`, runtime state и caches; повтор тестов из готовой папки.
- Screenshot/ручная визуальная приёмка пульсации и DPI не выполнены; геометрия и canvas-состояния проверены программно.

## Сохранение и ограничения

Один `LiveCreatorState.json` рядом с launcher, совместим с v0.4. Для перехода скопируйте свой state в папку v0.5 при закрытых приложениях; старый файл сохраните как резервный. В сборку пользовательский state не включён.
Пресеты остаются внешними абсолютными ссылками; отсутствующий файл показывает PRESET NOT FOUND; копий raw-файлов нет.
HARDWARE PRESETS, физические controllers/profiles и полноценное playback остаются заглушками. SEND TO DEVICE, STORE/0x28, SEQ ON/OFF и неподтверждённые Note/CC/SysEx не добавлены. HARDWARE PASS не заявляется.
Системный выбор папки остаётся нативным диалогом. Нумерация LOCAL относится к видимым preset rows и пересчитывается при раскрытии папок; не является hardware address.

## Изменённые файлы

- `live_creator/core/arrangement.py`: multi-delete и атомарный insert с gap до target slot.
- `live_creator/core/session.py`: удержание visual transport на конце до STOP.
- `live_creator/ui/layout.py`: Slots, pulse, text clip/wrap.
- `live_creator/ui/app.py`: timeline, drag preview, WORK AREA, pads, цвет, нумерация, Delete.
- `tests/test_session.py`, `tests/test_v05.py`, `tests/gui_smoke_v05.py`, `tests/build_live_creator.py`: regressions/упаковка. Старый `gui_smoke_v04.py` заменён; доступен в Git history.
- `AGENTS.md`, этот отчёт и новое ТЗ. Удаление предыдущего task-файла, уже сделанное пользователем, сохранено.
