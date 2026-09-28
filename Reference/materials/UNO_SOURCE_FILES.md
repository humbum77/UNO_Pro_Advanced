# UNO Pro Advanced — что добавить в источники проекта

Актуализировано: 2026-09-11.

## Минимальный постоянный комплект

1. `UNO_PROJECT_KNOWLEDGE.md` — главный актуальный контекст; читать первым.
2. Последний полный архив исходников редактора.
3. `PROJECT_STATE.md` — версия, статус сборки и текущий фокус.
4. `FIXED_CHANGES.md` — обязательные/замороженные решения.
5. `UNO_PROJECT_TASKS.md` — backlog и build gate.
6. `HARDWARE_TEST_RESULTS.md` — только результаты реального UNO.
7. `SYSEX_PROTOCOL.md` — confirmed/test/unknown команды.
8. `MIDI_REFERENCE.md` — официальные CC и hardware-tested raw values.
9. `STATE_0x37_MAP.md` и `STATE_0x37_PARAMETER_MAP.csv`.
10. Runtime `state_decoder_map.json`.
11. `PRESET_FLASH_FORMAT.md`.
12. `UPDATER_DFU_RESEARCH.md`.
13. `UNO_TEST_DATA_ALL.md` — полный сырой исследовательский архив.
14. `RESEARCH_INDEX.md`, `BUILD_RULES.md`, `GUI_SPEC.md`, `FILE_FORMATS_PATHS.md`.

## Крупные и бинарные доказательства

- `UNO_FULL_STATE_MAP_20260909_020500.json` — полный sweep 11 136 состояний.
- Все `uno_capture_*.txt`, `uno_monitor_capture_*.txt`, `uno_proxy_capture_*.txt`.
- `test2.unosyp`, `test3.unosyp`, `test4.unosyp`, `test5.unosyp`.
- `USP_FW_Main.dfu`.
- `USP_Presets.dfu`.
- `UNO Synth Pro Firmware Updater(1).exe`.
- Извлечённые payloads updater-а и отчёты с hashes/addresses.
- Скрипты Full State Mapper, monitor/proxy и DFU-analysis.
- `Docs/test_v158_regression.py`, `Docs/test_v159_working.py` и `VALIDATION_v158_RU.md`; после появления — `VALIDATION_v159_RU.md`.

## Что уже найдено среди сохранённых материалов

- `PROJECT_STATE.md`
- `FIXED_CHANGES.md`
- `HARDWARE_TEST_RESULTS.md`
- `UNO_PROJECT_TASKS.md`
- `SYSEX_PROTOCOL.md`
- `MIDI_REFERENCE.md`
- `STATE_0x37_MAP.md`
- `PRESET_FLASH_FORMAT.md`
- `UPDATER_DFU_RESEARCH.md`
- `RESEARCH_INDEX.md`
- `UNO_TEST_DATA_ALL.md`
- `UNO_FULL_STATE_MAP_20260909_020500.json`
- `Анализ проекта UNO Pro Advanced.docx`
- несколько capture-файлов и Python-модулей проекта.

## Требуют проверки физической доступности/повторного добавления

- `USP_FW_Main.dfu`.
- `USP_Presets.dfu`.
- `UNO Synth Pro Firmware Updater(1).exe`.
- Полный актуальный архив v1.59 working source.
- Все исходные capture, использованные для свежего разбора `0x3E`.
- Материалы последнего анализа write-команды updater-а и адресного UPLOAD `dfu-util 0.8`.

Если бинарник упоминался в старой ветке, это ещё не гарантирует доступ к его байтам в новом сеансе. Для воспроизводимого анализа он должен присутствовать отдельным источником.

## Порядок чтения для нового чата

1. `UNO_PROJECT_KNOWLEDGE.md`.
2. `PROJECT_STATE.md` + `FIXED_CHANGES.md`.
3. `HARDWARE_TEST_RESULTS.md`.
4. Тематический документ (`SYSEX_PROTOCOL`, `STATE_0x37_MAP`, `PRESET_FLASH_FORMAT` или `UPDATER_DFU_RESEARCH`).
5. Сырые capture/JSON/binary только для проверки конкретного вывода.

