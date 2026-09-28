# Подготовка UNO Pro Advanced v0.9.6-beta к отправке

Дата: 2026-09-15. Ветка: main. Репозиторий: https://github.com/humbum77/UNO_Pro_Advanced.git.

Публикуемая версия — **v0.9.6-beta**. `v0.10.0-alpha` было несогласованным локальным обозначением интеграции, не новой релизной линией. Старые локальные сборки сохраняются для истории, не отправляются как release. Исправление версии не меняет функциональность.

Актуальный архив: `builds/UNO_Pro_Advanced_v0.9.6-beta.zip`. Формат source standalone: Python 3.12+, Tkinter, Pillow. Commit содержится в BUILD_COMMIT внутри архива; CRC/SHA-256 manifest проверяется builder.

Общие документы из `D:\UNO\docs` включены в Git как `Docs/PROJECT_STATE.md` и `Docs/DECISIONS.md`. Корневой `D:\UNO\AGENTS.md` — локальные правила рабочего пространства; правила Git-проекта находятся в его собственном AGENTS.md.

## Перед отправкой

Локальные проверки исправления: 57 unittest, compile/import, отсутствие изменений runtime кроме номера, идентичность зеркал документации — PASS. Перепроверка GUI/запуска v0.9.6-beta заблокирована: прежняя тестовая Tcl/Tk-папка отсутствует, доступ к установленному Python/Tkinter отклонён системой approval. После восстановления доступа выполнить оба GUI smoke-теста и tests/launch_release.py с доступным Tkinter либо проверить run_editor.bat вручную. Предыдущий PASS интеграционной сборки не выдаётся за новый PASS beta.

В этом проходе push не выполняется, теги и GitHub Release не создаются. Обновление remote main через fetch не удалось из-за недоступности github.com:443. Поэтому отсутствие новых удалённых изменений пока НЕ подтверждено.

После восстановления доступа, из корня репозитория:

```powershell
git fetch origin main --no-tags
git log --oneline --left-right HEAD...FETCH_HEAD
git merge-base --is-ancestor FETCH_HEAD HEAD
```

Если последняя команда завершилась не с кодом 0, остановиться: сначала согласовать удалённые изменения, не делать force push. Если удалённая main является предком HEAD, после команды пользователя на отправку:

```powershell
git push origin main
```

Папка builds исключена из Git. Push исходников сам по себе не загрузит ZIP и не создаст GitHub Release. Архив v0.9.6-beta можно публиковать как отдельный release asset по отдельной команде. Не создавать тег для ошибочной alpha-версии и не переписывать существующую историю.

## Ограничения не изменились

Native automation entry mapping/writer PARTIAL, exact maximum и byte495 UNKNOWN; неподтверждённые шкалы/преобразования не дополняются догадками. Live playback software-only. EMPTY timing и marker collision остаются ограничениями. HARDWARE PASS и финальный ручной visual PASS не заявляются. Подробности: INTEGRATION_v0.9.6-beta.md.
