# Baseline — зафиксированный прогон проверок

Дата прогона: **2026-09-29**
Платформа: Windows, Python 3.14.7
Корень: `E:\UNO_Pro_Advanced`

## Команды

```
python -m compileall -q .                              # PASS
python -m unittest discover -s tests -p "test_*.py"     # 140 tests
```

## Результат

```
Ran 140 tests
FAILED (failures=4, skipped=4)
```

15 тестов добавлены 2026-09-29: `tests/test_matrix_codec.py` проверяет кодек
на реальных контрольных захватах из `tests/fixtures/UNO_UNIFIED_NORMALIZED_FINAL_2026-09-29.sqlite`.
Подробности — в `Docs/history/EVIDENCE_BASE.md`.

7 тестов добавлены 2026-09-29: `tests/test_automation_order.py` фиксирует
подтверждённый порядок автоматизации прибора. Подробности — в
`Docs/history/PARAMETER_SELECTION_2026-09-29.md`, раздел 7.

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
| `app.py:3737` | `slot` инициализируется до `try` — `UnboundLocalError` на битом 0x24 больше не выходит из приёмника | воспроизведение падения до правки |
| `app.py:3690` | `_drain_midi_rx` обёрнут в `try/finally` — опрос MIDI не может молча остановиться | — |
| `automation_metadata.py` | `AUTOMATION_ORDER` (23, порядок прибора), `STEP_PARAMETERS`; `NOISE` зарегистрирован как автоматизируемый; `VELOCITY` помечен как параметр шага | `tests/test_automation_order.py`, 7 тестов |
| `uno_step_automation_decoder.py` | `NOISE` перенесён с позиции 22 на позицию 9, между `LEVEL3` и `CUTOFF1`; порядок вынесен в `DECODER_PARAMETER_ORDER` | `tests/test_automation_order.py` |
| `tests/test_integration.py` | `test_no_guessed_automation_sends` обращается к полосе по имени `CUTOFF 1`, а не по индексу 0 | тест перестал зависеть от порядка списка |

## Проверка матрицы модуляции

`Mod N Amount` занимают FILE id `0x26..0x35` (38..53) и UI-порядок 33..48.
До правки список и словарь расходились на 4 позиции, и `ui_route_to_file_change`
писала индекс списка вместо FILE id: выбор «Mod 5 Amount» попадал в файл как
«Mod 1 Amount». Скрытые назначения остаются читаемыми.

## Чего здесь нет

`.git` в сборке нет — тест `test_safety_unchanged` не может выполниться.
GUI smoke не выполнялся: требует интерактивного дисплея Windows.
HARDWARE PASS не заявляется — физическое устройство в этой сборке не проверялось.
