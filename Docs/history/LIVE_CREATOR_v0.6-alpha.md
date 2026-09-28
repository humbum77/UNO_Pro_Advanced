# Live Creator v0.6-alpha

Standalone source release для Python 3.10+ с Tkinter, не автономный EXE.
Подготовлен по отдельной команде пользователя «сделай сборку» после review-итерации.
Ветка: `live-creator`; основной проект и main не изменяются.

## Запуск

Распаковать ZIP целиком и запустить `run_live_creator.bat`.
Альтернатива: `python -m live_creator` из каталога релиза.
State: `%LOCALAPPDATA%\UnoLive\state\live_creator_state.json`.
Старый state рядом с launcher автоматически не переносится. Для ручного переноса закрыть приложение, сохранить резервную копию старого и нового state; формат v1 читается. Исходные `.unosyp` остаются на прежних местах.

## Изменения

- Независимые selected song/block и playing snapshot; явная playback state machine.
- Назначенный Loop без прыжка, естественный вход, PLAY в активном Loop снимает цикл и продолжает песню.
- Единый Timeline 64 steps с отображением 32+32; один объект блока на границе строк; разные MOVE/RESIZE previews.
- Markers как начала секций, объектные меню, внутренний clipboard без markers при копировании блока.
- Общая popup-палитра, независимые цвета песни/блока, цветное центрированное NAME, компактный TEMPO.
- Заметная пульсация заливки без мерцания текста, независимая рамка выбора.
- Подтверждённая Sequence Length: байты 207–208, `(value + 1) // 8`; шаг 1/16 ноты. Duration учитывает длину, повторы и tempo, не включает Loop.
- Общий state UnoLive; служебные данные не создаются в LOCAL PRESETS.

Подробности реализации и визуальные результаты: `LIVE_CREATOR_REVIEW.md`.
Галерея исходного worktree: `Docs/REVIEW_GALLERY.md`; изображения не включены в компактный release.

## Проверки выпуска

Перед упаковкой: compile/import, 44 unittest, Tk GUI smoke, git diff --check и проверка ветки.
После упаковки: повторные unittest/GUI smoke из release, CRC ZIP, SHA-256 каждого файла по MANIFEST.json, проверка состава и BUILD_COMMIT.
Точный commit записан в `BUILD_COMMIT` рядом с launcher.

## Ограничения

- Playback — только software, без звука/MIDI. HARDWARE PRESETS и физические контроллеры не подключены. HARDWARE PASS не заявляется.
- Музыкальная длительность EMPTY не согласована: неизвестное DURATION вместо догадки; playback такой песни не запускается.
- Конфликт переноса разных markers на одну позицию отменяет операцию целиком. Автоматического объединения через `/` нет — known issue.
- Правки редактора применяются при следующем старте, не меняют текущий playback snapshot.
- Automation Editor и новые automation mapping в этот выпуск не входят.
- Видимость исправленного marker-conflict warning проверена программно; финальная ручная визуальная проверка этого warning не завершена.
- STORE/0x28, неизвестный SEQ ON/OFF и запись hardware SONG не затрагивались.
