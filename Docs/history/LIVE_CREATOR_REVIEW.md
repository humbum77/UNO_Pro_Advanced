# Live Creator — результат review-итерации

Основа: v0.5-alpha, commit `41e8a4f3fa90aeb27022a7646348c26301871195`.
Работа выполнена только в `D:\UNO\Live-Creator`, ветка `live-creator`. Новый release/ZIP/EXE не создавался; новый commit до приёмки не делался.

## Что реализовано

- Один Timeline до 64 Song Steps на песню; две визуальные строки 32+32. Split block имеет один ID, selection, цвет, операции и playback indication.
- 64 независимые песни; editor selection отдельно от playing song snapshot. Выбор другого pad/block не запускает и не останавливает playback. Структурные изменения редактора не мутируют уже запущенный snapshot.
- Явная state machine STOPPED/COUNTDOWN/PLAYING; отдельно NONE/ASSIGNED/ACTIVE для Loop. Назначение будущего loop не прыгает; natural entry активирует цикл. PLAY в active loop снимает loop и продолжает с той же позиции. Следующее нажатие вне loop останавливает.
- Countdown OFF/5/10/15/30/45/60, отмена повторным нажатием, Space с защитой текстового ввода.
- Markers — начала секций до следующего marker/конца песни. Флажки над блоками, список MARKERS с номерами Song Step и навигацией; Set/Delete Marker через ПКМ.
- Внутренний clipboard блоков и песен: reference/length/color/parameters, глубокое копирование без aliases; block clipboard не содержит markers. Cut/Delete не трогают `.unosyp`.
- Общие тёмные popup-компоненты: object menu, палитра 52 цветов, небольшой marker prompt. Disabled команды различимы. В меню pad нет marker/loop действий.
- Цвета song и block независимы; NAME окрашен в song color, текст центрирован и контрастный. TEMPO расположен рядом с label. Постоянная COLOR-палитра убрана.
- MOVE: приглушённый источник, полупрозрачный snapped ghost. RESIZE: anchored fill, изменённые slots и яркая граница; без ghost-заливки всего блока. Белых MOVE-стрелок и moving playhead нет.
- Общая пульсация заливки pad/block: hue сохраняется, меняется luminance; текст не мерцает. Оранжевый selection border независим.
- Один общий state v2, обратное чтение v1. Default path: `%LOCALAPPDATA%\UnoLive\state\live_creator_state.json`; атомарная запись. В LOCAL PRESETS нет service writes.

## Подтверждённый Sequence Length и время

Основание — исследование пользователя, переданное в чате и research handoff. Отдельно пользователь подтвердил 1/16-note sequencer step.

```
value = data[207] | (data[208] << 7)
sequence_length = (value + 1) // 8
seconds_per_sequence = sequence_length / 4 * 60 / tempo
block_duration = seconds_per_sequence * block.length
```

Проверены в synthetic regression контрольные длины 1, 2, 4, 8, 9, 10, 16, 17, 32, 33, 48, 64. Это программная проверка переданного подтверждения, не новое самостоятельное hardware исследование.
Read-only adapter проверяет 297-byte/7-bit state framing и допустимый диапазон длины, не изменяет исходные байты. JSON/software presets требуют явных length/resolution и confirmed metadata; нераспознанный формат не подменяется догадкой.
Loop не добавляется к DURATION. ELAPSED/REMAINING относятся к номинальной структуре snapshot и не накапливают число повторов. Очень короткая подтверждённая sequence может естественно завершиться быстро — искусственного продления PLAY нет.

## Визуальная проверка

Использовались реальные Tk-окна установленного Python и computer-use, не HTML-макеты. Для UI-приёмки подготовлены изолированные синтетические `.unosyp`-fixtures с явной музыкальной длиной; они не являются hardware captures. Скриншоты находятся в `Docs/review-evidence`.

- Основной экран, перенос через 32/33, markers, NAME/TEMPO — просмотрены.
- Оба меню и палитра открыты реальными кликами; применение цвета к pad/NAME просмотрено.
- Назначенный loop: dashed underline. Playback естественно дошёл до начала range; active loop показан solid underline. PLAY снял loop, elapsed продолжил движение без сброса.
- Пульсация просмотрена на тёмном, среднем и светлом цветах. После первой проверки чрезмерный уход в белый исправлен. Актуальные кадры — серии `12-dark`, `13-medium`, `14-bright`.
- MOVE и RESIZE показаны как подготовленные промежуточные состояния настоящих drag handlers, а не завершённая ручная drag-сессия. Финальный RESIZE — `18-resize-final.png`.
- Проверка показала, что warning о marker collision вытеснялся scrollbar из WORK AREA. Исправлен minimum requested height scrollbar; видимость warning подтверждена повторным GUI-тестом. Финальный дополнительный запуск сцены был отклонён системой approval review из-за лимита, поэтому **финального визуального PASS для warning нет**. Старый `17-marker-known-issue.png` не доказывает видимость исправленного warning.

См. `Docs/REVIEW_GALLERY.md` для ссылок на конкретные изображения.

## Regression results

- **44 unittest — PASS**: базовый ripple/limit/reference/state, transport lifecycle, timing, assigned→active→exit loop, snapshot isolation, markers, clipboard, anchored left resize, decode lengths, global path.
- **Tk GUI review smoke — PASS**: оба меню/disabled state, палитра, NAME, markers/clipboard, context-sensitive Ctrl+X/C/V/Del, text guard, независимость song selection, warning visibility, три размера окна, 32+32, квадратные pads, отсутствие service files в preset fixtures.
- Compile/import и `git diff --check` проверяются перед передачей. Основной inherited `app.py` не изменяется; main ref остаётся `51906bc1a40a636441c98f10794113d696ffc180`.
- Никаких MIDI/device sends в Live Creator не добавлено. **HARDWARE PASS не заявляется.**

## Known issues / что не завершено

1. **Конфликт markers.** Если удаление блока переносит marker на следующий блок, где уже есть другой marker, операция отклоняется целиком с `Marker conflict ... operation cancelled`. Оба текста и timeline сохраняются. Не объединяем через `/`. Правило разрешения такого конфликта требует решения пользователя.
2. **Музыкальная длительность EMPTY.** Его геометрия точна, но единица музыкального времени пустого Song Step пока не согласована. Песня с таким gap показывает неизвестное DURATION, playback не запускается с выдуманным временем. Для обычных распознанных бинарных presets Length и 1/16 уже используются.
3. Playback пока software/model-only: нет звука, применения presets, hardware reading, физического controller или hardware SONG writes.
4. Изменения редактора после старта вступают в playback только при следующем запуске snapshot. Это сохраняет независимость editor/playing state, но не является live-edit deployment на устройство.
5. В новом локальном `...TZ_v2.md` и research handoff появились требования Automation Editor. Они прочитаны как дополнительные материалы; в текущем standalone Automation Editor отсутствует. Новое automation UI и decoder/encoder в этом UI/playback проходе **не добавлялись**. Подтверждения polarity не превращались в выдуманные binary mappings.
6. Старый state рядом с launcher не переносится автоматически: v1 читается, но для перехода нужно при закрытом приложении сохранить резервную копию и перенести его в новый общий путь. Исходные presets переносить/копировать не нужно.

## Файлы

Изменены: `live_creator/core/arrangement.py`, `session.py`, `state.py`; `live_creator/ui/app.py`, `layout.py`; `tests/test_session.py`, `tests/test_v05.py`, `tests/gui_smoke_v05.py` (compatibility entrypoint); `AGENTS.md`, `.gitignore`.
Добавлены: `live_creator/core/clipboard.py`, `paths.py`; `live_creator/devices/uno/timing.py`; `live_creator/ui/popups.py`; `tests/test_review_model.py`, `gui_smoke_review.py`, `review_preview.py`; этот отчёт и visual evidence.
Task/recommendation/research-файлы, появившиеся у пользователя во время работы, не переписывались; удалённый пользователем старый task не восстанавливался.

Следующий шаг — пользовательская приёмка. Сборку выполнять только по отдельной явной команде, не перезаписывая v0.5-alpha.
