# UNO Pro Advanced — актуальный справочный комплект

Дата: 2026-09-12. Базовая сборка: v1.64.

## Читать в таком порядке

1. `PROJECT_STATE.md` — текущая версия и состояние функций.
2. `FIXED_CHANGES.md` — обязательные и замороженные решения.
3. `HARDWARE_TEST_RESULTS.md` — результаты физического UNO.
4. `SYSEX_PROTOCOL.md` — подтверждённые, тестовые и неизвестные команды.
5. `MIDI_REFERENCE.md` — MIDI CC и аппаратные значения.
6. `STATE_0x37_MAP.md` и `STATE_0x37_PARAMETER_MAP.csv` — карта state dump.
7. `PRESET_FLASH_FORMAT.md` — структура пресетов/flash.
8. `UPDATER_DFU_RESEARCH.md` — DFU и updater.
9. `GUI_SPEC.md` — закреплённое поведение интерфейса.
10. `UNO_PROJECT_TASKS.md` — незавершённые задачи.
11. `UNO_TEST_DATA_ALL.md` и `RESEARCH_INDEX.md` — исследовательская история и индекс доказательств.
12. `BUILD_RULES.md`, `BUILD_NOTES_v1.64.md`, `FILE_FORMATS_PATHS.md` — правила выпуска и структура файлов.

## Официальная документация

- `UNO_Synth_Pro_User_Manual.pdf`
- `UNO_Synth_Pro_Editor_User_Manual.pdf`
- `UNO_Synth_Pro_MIDI_Chart.pdf`

Официальная документация подтверждает публичное поведение устройства, но не заменяет аппаратные capture при реверс-инжиниринге закрытого SysEx.

## Правило достоверности

- `CONFIRMED/HARDWARE PASS` — подтверждено физическим UNO или контролируемым capture.
- `IMPLEMENTED` — реализовано программно, аппаратная проверка может отсутствовать.
- `TEST/PROVISIONAL` — кандидат для безопасного тестирования.
- `RESEARCH/NOT CONFIRMED` — гипотеза, не использовать как готовую карту протокола.

Более позднее прямое подтверждение пользователя имеет приоритет перед устаревшим документом. Неизвестные значения и команды не угадывать.
