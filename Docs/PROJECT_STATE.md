# UNO Pro Advanced — состояние проекта

Дата фиксации: 2026-09-15.

## Актуальная линия

- Основной проект: `D:\UNO\project_unified`, ветка `main`.
- Текущая версия: **v0.9.6-beta**, кумулятивно после v0.9.5-beta.
- База main: `51906bc1a40a636441c98f10794113d696ffc180`; Live Creator: `e2b0a977d194fdf28e40eaac73b1eaae8de525b0`.
- Интеграционный merge: `2a63c2684c89881003bdd015cc24a58dbde11e95`. Его прежнее название v0.10.0-alpha было ошибочным и исправляется отдельным commit без переписывания истории.
- Версия standalone Live Creator v0.6-alpha не меняет beta-статус основной программы.
- Отдельный worktree Live-Creator и его пользовательские материалы не изменяются.

## Реализовано в интеграции

Встроенный LIVE: 64 независимые песни, Timeline 32+32, LENGTH 1–64 без удаления блоков, скругление 4px, независимый выбранный и проигрываемый контекст, clipboard/markers/Loop/pulse.
Sequencer: Dupl с удвоением длины и копированием декодированной automation, прежний Fill.
Automation: parameter selector, индивидуальная metadata шкал и read-only native container reader.
Dark/Light темы, неизменные transport green/red, Settings/Theme icons. Служебные данные — `%LOCALAPPDATA%\UnoLive`, не LOCAL PRESETS.

## Проверки и границы подтверждения

57 актуальных unittest повторно прошли при исправлении версии; compile/import и version-only runtime diff также PASS. Два Tk GUI smoke-теста и packaged main проходили до переименования, но повторная проверка beta заблокирована отсутствием прежней Tcl/Tk-папки и отклонённым доступом к установленному Python. Новый GUI/launch PASS не заявляется; требуется повторная проверка после восстановления среды. При автоматическом запуске используется mocked MIDI и временное хранилище.
На предоставленных файлах из `D:\UNO\materials\test` проверены 6 automation containers и 12 Sequence Length. Это SOFTWARE validation реальных captures, не новое аппаратное испытание.
Исторические аппаратные результаты основной beta-линии не являются HARDWARE PASS новой интеграционной сборки.
Старый Docs/test_beta.py содержит несовместимые проверки отсутствующих в исходной базе API и старого SONG UI; подробности в отчёте.
Финальный ручной visual PASS не получен из-за ограничения инструмента.

## PARTIAL / UNKNOWN / UNVERIFIED

- Native automation: parameter/value/step packing и writer PARTIAL; byte495 и аппаратный MAX entries UNKNOWN. Не устанавливать MAX=17.
- Dupl блокируется при opaque native automation, чтобы не терять события.
- Tune hybrid, Wave normalization, mode-aware LFO и raw CC → device-unit conversion не дополняются догадками.
- Live playback без MIDI/звука/controllers/hardware SONG writes.
- Музыкальная длительность EMPTY неизвестна; конфликт markers отменяет edit без объединения через /.
- STORE/0x28 locked; неизвестный SEQ ON/OFF не изменён.
- Выборочные исторические ограничения hardware 0x29 не считаются закрытыми этой интеграцией.

## Сборка и отправка

Актуальный артефакт: `D:\UNO\project_unified\builds\UNO_Pro_Advanced_v0.9.6-beta.zip`.
Source standalone для Python 3.12+, Tkinter, Pillow, не автономный EXE. Source hash — BUILD_COMMIT внутри архива.
Старую локальную v0.10.0-alpha не публиковать; она сохранена как superseded artifact.
Push/создание тегов/публикация GitHub Release пока не выполняются. Remote main не удалось проверить из-за отсутствия соединения с GitHub; перед push повторить fetch и ancestry check, не использовать force push.

## Документация

Актуальные материалы в основном repo: `Docs/INTEGRATION_v0.9.6-beta.md`, `Docs/RELEASE_PREPARATION.md`, `CHANGELOG.md`, `AGENTS.md`.
Этот файл и DECISIONS.md зеркалируются из `D:\UNO\docs` в `D:\UNO\project_unified\Docs`, чтобы общие решения были доступны и на GitHub.
