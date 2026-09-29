# Baseline — зафиксированный прогон проверок

Дата прогона: **2026-09-29**
Платформа: Windows, Python 3.14.7
Корень: `E:\UNO_Pro_Advanced`

## Команды

```
python -m compileall -q .                              # PASS
python -m unittest discover -s tests -p "test_*.py"     # 170 tests
```

## Результат

```
Ran 170 tests
FAILED (failures=4, skipped=4)
```

15 тестов добавлены 2026-09-29: `tests/test_matrix_codec.py` проверяет кодек
на реальных контрольных захватах из `tests/fixtures/UNO_UNIFIED_NORMALIZED_FINAL_2026-09-29.sqlite`.
Подробности — в `Docs/history/EVIDENCE_BASE.md`.

7 тестов добавлены 2026-09-29: `tests/test_automation_order.py` фиксирует
подтверждённый порядок автоматизации прибора. Подробности — в
`Docs/history/PARAMETER_SELECTION_2026-09-29.md`, раздел 7.

1 тест добавлен 2026-09-29: `test_step_automation_integration.
test_instrument_produces_more_than_sixteen_lanes` фиксирует, что прибор пишет
17 полос на шаг, и пропускается, если съёмки `AUTO_L2.unosyp` нет рядом.

2 теста добавлены 2026-09-29: `test_automation_order.
test_unordered_automatable_parameters_are_registered_and_flagged` и
`test_panel_appends_unordered_after_the_confirmed_order` — набор
автоматизируемых параметров шире подтверждённых 23; позиции остальных помечены
`UNKNOWN` и не выдаются за подтверждённые.

1 тест добавлен 2026-09-29: `test_automation_order.
test_menu_only_parameters_are_flagged_uncapturable` — 12 параметров, доступных
только через меню прибора, помечены «чистый снимок невозможен» и не могут
получить тесты на основе снимков.

9 тестов добавлены 2026-09-29: `tests/test_tune_scale.py` фиксируют грамматику
подписи шкалы TUNE, подтверждённую оператором. Подробности — в
`Docs/history/TUNE_SCALE_2026-09-29.md`.

4 теста добавлены 2026-09-29: `test_tune_scale.TuneNativeCodec` фиксируют
кодек TUNE (2 байта, старшим первым, центы), выразимость полосы
`1st1c`..`1st99c`, чтение `пара/16 = центы` по смещению `0x01F1` на контрольных
съёмках `99C`/`1ST`/`2ST` и наличие значения 146c (`1st46c`) в `DHK_Y.unosyp`.
Последние два пропускаются, если съёмок рядом нет.

9 тестов добавлены 2026-09-29: `tests/test_matrix_operator_lists.py` сверяют
реестр матрицы со списками назначений и источников, переданными оператором
2026-09-29: 54 назначения и 38 источников совпадают по file id, wire id и
семантике. Подробности — в `Docs/history/MATRIX_OPERATOR_LISTS_2026-09-29.md`.

3 теста добавлены 2026-09-29 в тот же файл: UI-порядок источников равен
порядку прибора, выпадающий список `app.py` берётся из кодека, и **каждая
подпись селектора резолвится в FILE id** — последний и есть проверка, которая
поймала неписавшиеся четыре источника.

Подробно:

| Тест | Тип | Причина |
|------|-----|---------|
| `test_integration.test_safety_unchanged` | FAIL | закреплён за коммитом `51906bc`, который есть в репозитории, но **не является предком HEAD** — пришёл из слитой линии `main.zip`, где `midi_engine.py` был заглушкой в 57 байт против 3443 сейчас. Причина изменилась: до появления `.git` это был ERROR |
| `test_integration.test_theme` | FAIL | ожидает прежний Light accent swap; тема в текущем коде одна |
| `test_v05.test_boundary_segments` | FAIL | **регресс против ТЗ** — см. ниже |
| `test_v05.test_slots_fit` | FAIL | **регресс против ТЗ** — см. ниже |
| 4 теста | skip | требуют внешних captures/файлов |

## Регрессии, требующие решения

`AGENTS.md` и `PROJECT_STATE.md:61` фиксируют Timeline как две строки
`01–32` и `33–64` без горизонтальной прокрутки. `live_creator/ui/layout.py:12`
вычисляет `pitch = (width - 2*margin) / 16` при 64 шагах, поэтому вся полоса
вчетверо шире вьюпорта и требует прокрутки:

```
width=1176 → pitch=72.2  total_width=4644  (x шага 64 = 4562)
```

- `test_boundary_segments` ждёт `[(30,32),(33,35)]` — две строки; код возвращает `[(30,35)]`
- `test_slots_fit`: правая граница шага 64 = 983 при лимите 927

**Статус: UNRESOLVED.** Код, документация и тесты описывают три разных варианта.
Это не устаревшее ожидание теста, а расхождение с собственным ТЗ. Решение
(вернуть две строки или переписать ТЗ под одну прокручиваемую полосу) —
за пользователем. До решения статус `PARTIAL`, а не `PASS`.

## Исправления, внесённые при сборке 2026-09-29

| Файл | Что | Проверка |
|------|-----|----------|
| `matrix_codec.py` | переписан на чтение `UNO_MATRIX_FULL_REGISTRY.csv`; FILE id и UI-порядок больше не могут разойтись | 16/16 маршрутов round-trip, проверка реестра ловит битый файл |
| `UNO_MATRIX_FULL_REGISTRY.csv` | UI-порядок 38 источников приведён к порядку прибора: 17 строк, только столбец `ui_position_0based` | 15/15 тестов кодека без изменений; file id, wire id, семантика и флаги выбора не тронуты |
| `UNO_MATRIX_FULL_REGISTRY.csv` | названия `CV 1 IN`, `GATE 1 IN`, `CV 2 IN`, `GATE 2 IN` приведены к написанию прибора; **было: четыре источника не писались** — `ValueError: unknown Matrix entry` | все 38 источников и 54 назначения резолвятся; `test_the_cv_and_gate_in_sources_are_writable` |
| `app.py:27` | ручной список `MATRIX_SOURCES` удалён, список берётся из `matrix_codec.MATRIX_SOURCE_FILE_NAMES` | `test_editor_source_selector_follows_the_registry` |
| `matrix_codec.py:104` | `MATRIX_SOURCE_FILE_NAMES` упорядочен по `ui_index` явно | — |
| `tests/test_matrix_codec.py` | фикстуры `expected_source` приведены к новому написанию | 15/15 проходят |
| `app.py:3737` | `slot` инициализируется до `try` — `UnboundLocalError` на битом 0x24 больше не выходит из приёмника | воспроизведение падения до правки |
| `app.py:3690` | `_drain_midi_rx` обёрнут в `try/finally` — опрос MIDI не может молча остановиться | — |
| `automation_metadata.py` | `AUTOMATION_ORDER` (23, порядок прибора), `STEP_PARAMETERS`; `NOISE` зарегистрирован как автоматизируемый; `VELOCITY` помечен как параметр шага | `tests/test_automation_order.py`, 7 тестов |
| `uno_step_automation_decoder.py` | `NOISE` перенесён с позиции 22 на позицию 9, между `LEVEL3` и `CUTOFF1`; порядок вынесен в `DECODER_PARAMETER_ORDER` | `tests/test_automation_order.py` |
| `tests/test_integration.py` | `test_no_guessed_automation_sends` обращается к полосе по имени `CUTOFF 1`, а не по индексу 0 | тест перестал зависеть от порядка списка |
| `automation_metadata.py` | `MAX_AUTOMATION_LANES_PER_STEP=20` — единственный источник истины для предела полос на шаг | `test_device_limit_is_twenty_entries` сверяет все четыре места |
| `app.py:3200,3201,3209` | кап 16 заменён на константу; **16 отказывал прибору** — `AUTO_L2.unosyp` даёт 17 полос на шаге 1 | `test_instrument_produces_more_than_sixteen_lanes` |
| `uno_step_automation_decoder.py`, `native_automation.py` | предел берётся из общей константы вместо двух хардкодов | разбор 294 файлов при границах 18 и 20 даёт идентичный результат |
| `automation_metadata.py` | `AUTOMATION_UNORDERED` — 15 автоматизируемых параметров вне бенчмарка, все со статусом `AUTOMATABLE: order position UNKNOWN`; статус `FM 1`/`FM 2` исправлен с «не автоматизируется» | 2 теста в `test_automation_order.py` |
| `app.py:15` | импорт `MAX_AUTOMATION_LANES_PER_STEP` | — |
| `automation_metadata.py` | `AUTOMATION_NO_CAPTURE` — 12 параметров, доступных только через меню прибора; чистые снимки для них невозможны, тесты на них запрещены | `test_menu_only_parameters_are_flagged_uncapturable` |
| `automation_metadata.py` | `FILTER ENV ATTACK/DECAY/SUSTAIN/RELEASE` зарегистрированы впервые (CC 53–56) | тот же тест |
| `automation_metadata.py` | `FM 1`/`FM 2` переведены в группу неснимаемых; оба прочтения «filter fm» остаются зарегистрированы | тот же тест |
| `automation_metadata.py` | `tune_label()` — грамматика подписи шкалы TUNE; `Parameter` получил `formatter` и `format()`; TUNE 1/2/3 переведены с `'st'` на приборную грамматику | `tests/test_tune_scale.py`, 9 тестов, полная лестница из 2401 значения |

## Проверка матрицы модуляции

`Mod N Amount` занимают FILE id `0x26..0x35` (38..53) и UI-порядок 33..48.
До правки список и словарь расходились на 4 позиции, и `ui_route_to_file_change`
писала индекс списка вместо FILE id: выбор «Mod 5 Amount» попадал в файл как
«Mod 1 Amount». Скрытые назначения остаются читаемыми.

## Чего здесь нет

`.git` в сборке нет — тест `test_safety_unchanged` не может выполниться.
GUI smoke не выполнялся: требует интерактивного дисплея Windows.
HARDWARE PASS не заявляется — физическое устройство в этой сборке не проверялось.
