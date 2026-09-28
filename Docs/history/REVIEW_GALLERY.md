# Live Creator — визуальный просмотр до сборки

Реальные окна приложения на изолированных тестовых данных. Это не новая сборка и не аппаратный playback.

## Основной экран, Timeline, Markers, NAME и TEMPO

![Основной экран](D:/UNO/Live-Creator/Docs/review-evidence/01-main.png)

## Объектные меню и общая палитра

Song pad:

![Меню песни](D:/UNO/Live-Creator/Docs/review-evidence/02-song-menu-1.png)

Timeline Block:

![Меню блока](D:/UNO/Live-Creator/Docs/review-evidence/05-block-menu-1.png)

Общая палитра:

![Палитра](D:/UNO/Live-Creator/Docs/review-evidence/03-palette-1.png)

[Применение цвета к pad и NAME](D:/UNO/Live-Creator/Docs/review-evidence/04-name-color.png)

## Assigned / Active Loop

- [Назначенный Loop — пунктир](D:/UNO/Live-Creator/Docs/review-evidence/06-loop-assigned.png)
- [Playback естественно вошёл в Loop — сплошная линия](D:/UNO/Live-Creator/Docs/review-evidence/09-loop-active.png)
- [PLAY снял Loop, playback продолжился](D:/UNO/Live-Creator/Docs/review-evidence/10-loop-exit-continue.png)

Эти кадры сняты до окончательного уменьшения чрезмерного ухода пульсации в белый. Актуальные цвета в следующем разделе.

## Реальные фазы пульсации после корректировки

Кадры каждой пары сняты с интервалом около 600 ms. Заливка блока и pad меняет яркость, текст и selection border сохраняются. Здесь показаны кадры, не запись видео.

| Цвет | Фаза A | Фаза B |
|---|---|---|
| Тёмный | [Открыть](D:/UNO/Live-Creator/Docs/review-evidence/12-dark-phase-a.png) | [Открыть](D:/UNO/Live-Creator/Docs/review-evidence/12-dark-phase-b.png) |
| Средний | [Открыть](D:/UNO/Live-Creator/Docs/review-evidence/13-medium-a.png) | [Открыть](D:/UNO/Live-Creator/Docs/review-evidence/13-medium-b.png) |
| Светлый, блок через 32/33 | [Открыть](D:/UNO/Live-Creator/Docs/review-evidence/14-bright-a.png) | [Открыть](D:/UNO/Live-Creator/Docs/review-evidence/14-bright-b.png) |

## MOVE и RESIZE

Подготовленные промежуточные состояния настоящих drag handlers, до отпускания мыши.

MOVE: ghost смещён, исходное место приглушено.

![MOVE](D:/UNO/Live-Creator/Docs/review-evidence/15-move.png)

RESIZE: блок закреплён, подсвечены добавленные slots и активная граница; это не MOVE ghost.

![RESIZE](D:/UNO/Live-Creator/Docs/review-evidence/18-resize-final.png)

## Known issue: конфликт markers

Пример: INTRO начинается на первом блоке, VERSE — на следующем. Удаление первого блока попыталось бы поместить оба marker на одну позицию.

Пока операция отменяется целиком: `Marker conflict ... operation cancelled; resolve markers first`. Никакого автоматического `/` и потери текста. Видимость предупреждения после исправления scrollbar подтверждена GUI-тестом; финальный снимок warning не получен из-за отказа системы разрешений на дополнительный запуск. Не выдаём старый снимок без warning за подтверждение исправления.

[Полный отчёт, проверки и ограничения](D:/UNO/Live-Creator/Docs/LIVE_CREATOR_REVIEW.md)
