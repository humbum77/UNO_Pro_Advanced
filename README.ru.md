# UNO Pro Advanced v0.10.0-alpha

Интеграция main v0.9.5-beta и Live Creator v0.6-alpha: встроенная страница LIVE, LENGTH, скруглённые блоки, Dupl, parameter Automation, read-only native reader и общие Dark/Light темы.
Актуальный [отчёт с проверками и ограничениями](Docs/INTEGRATION_v0.10.0-alpha.md), [changelog](CHANGELOG.md).
Служебное хранилище: `%LOCALAPPDATA%\UnoLive`. Пользовательские presets не переносятся.
Это source standalone для Python/Tkinter/Pillow, не автономный EXE. Native automation writer/mapping остаются PARTIAL; Live playback без MIDI/звука. Hardware PASS не заявляется.

## Сохранённое поведение основной программы

Возвращены масштабирование 100/125/150 и кнопка ⛶. Первый запуск — 100%; дальнейший выбор сохраняется.
В Sequencer восстановлены прежний FILL и подсказка. SAVE и SAVE AS — только в верхней панели.
SAVE работает как в FIX2: имя и новая копия в стандартной папке пресетов. SAVE AS сохраняет отдельную копию в выбранный файл. Новый механизм рабочей папки, текущего файла и предупреждений отменён.

Windows, Python 3.12+, Pillow. Запуск: run_editor.bat.
STORE заблокирован; SEQ ON/OFF не изменён; preset 2 / 0x29 остаётся известным ограничением.

[Изменения](Docs/RELEASE_NOTES_v0.9.2-beta.md) · [Проверки](Docs/VALIDATION_v0.9.2-beta.md)
