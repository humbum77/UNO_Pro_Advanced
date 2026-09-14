# Live Creator — ТЗ следующей итерации

**Заменяет конфликтующие пункты предыдущего ТЗ.**

## Границы
Работать только `D:\UNO\Live-Creator`, ветка `live-creator`. Не трогать `D:\UNO\project_unified` и `main`.

Сохраняется: один режим; GRID 8×8 = 64 независимых песни; общий state/settings; LOCAL/HARDWARE presets; без SONG PRESETS, NEW/OPEN/SAVE и SEND TO DEVICE; hardware/MIDI mapping не придумывать.

## WORK AREA
Пока только song-level. Block-info section убрать полностью.

Порядок:
```text
[ PLAY ]

PLAY DELAY       [ OFF ▼ ]

NAME
[ My Song                  ]

TEMPO            [120]
DURATION         03:42
STEPS            48 / 64
BLOCKS           12
```

- PLAY/STOP наверху.
- PLAY DELAY сразу под ним: label и dropdown в одной строке.
- `OFF | 5 s | 10 s | 15 s | 30 s | 45 s | 1 min`, default OFF.
- NAME: label над широким input.
- TEMPO: label + узкий input примерно на 3 цифры в одной строке.
- DURATION/STEPS/BLOCKS оставить.
- отдельный STATUS/READY убрать.
- добавить выбор persistent song color в WORK AREA.

## PLAY bug
Сейчас PLAY после нажатия визуально/функционально сразу «отскакивает». Диагностировать фактическую причину и исправить state lifecycle, не маскировать задержкой. stopped=`PLAY`, playing=`STOP`. Space = PLAY/STOP (не перехватывать пробел при вводе текста).

Старт: selected Timeline block → с него; иначе с начала selected song. Клик другого pad во время playback меняет только editor selection и не останавливает/не запускает песню.

## TIMELINE: 32 + 32
Переделать Timeline в фиксированные две строки:
- row 1 = slots `01–32`;
- row 2 = slots `33–64`;
- вся 64-step песня видна одновременно;
- обе строки одинакового масштаба;
- каждый slot одинаковой фиксированной ширины;
- горизонтальный scroll для просмотра 64 steps не нужен.

Добавить тонкие вертикальные slot-grid lines. Можно немного сильнее обозначить 8/16/24/32 и 40/48/56/64, не перегружая UI.

Block, пересекающий 32/33 (например 30–35), визуально переносится на вторую строку двумя связанными сегментами, но в data model остаётся одним block, одной selection и одной операцией.

## Размер/рендеринг blocks
Blocks сделать компактнее текущей сборки:
- уменьшить высоту;
- подобрать base slot width под 32 slots в строке;
- сохранить читаемость хотя бы начала preset name;
- длинные имена clip/ellipsis, полный текст можно tooltip;
- ровные borders/padding;
- корректные normal/selected/playing/loop states;
- никаких наложений текста/диапазонов.

Не задавать слепо конкретные пиксели: цель — 32 slots в строке при приемлемой читаемости.

## EMPTY
Не сжимать EMPTY относительно сетки. При фиксированной grid:
- 1 EMPTY step = 1 slot;
- N EMPTY steps = N slots.
EMPTY визуально лёгкий/нейтральный, но геометрически занимает точные slots.

## Playback indication
Moving playhead полностью убрать.

Playing Timeline block:
- немного ярче;
- мягкая медленная пульсация;
- текст не мигает/не исчезает.
Selected и Playing — независимые состояния. Если оба одновременно, оба видны.

## MOVE arrows
Белые hover MOVE arrows убрать. Текущее обычное dragging blocks уже управляет EMPTY. Сохранить нормальный drag, resize при необходимости, ripple и EMPTY behavior.

## Удаление block
Добавить:
- `Delete / DEL` для selected block(s);
- Right Click context menu → `Delete`.
Не добавлять постоянную Delete button. После удаления не должно быть broken selection/render artifacts; соблюдать существующую ripple model.

## LOCAL PRESETS
Добавить нумерацию локальных presets отдельной компактной колонкой, не частью имени:
```text
001  _CMKV
002  _EXP
003  _EXT
```

## Drag PRESET → TIMELINE
Визуализировать drag:
- ghost/preview перетаскиваемого preset/block;
- подсветка target slot/position;
- snap к slot grid;
- до drop должно быть видно место результата;
- визуально различать `INSERT` между blocks и `REPLACE` существующего block.

## GRID pads
Pads оставить квадратными. Специально сейчас не уменьшать: после Timeline 32+32 доступная высота GRID естественно уменьшится, и квадратные pads станут компактнее.

### Empty pad
- только номер `01–64`;
- никаких `Empty`, `Song 01`, placeholder names;
- тёмный нейтральный фон.

### Filled pad
- номер исчезает полностью;
- показывается только song name;
- текст центрирован;
- word-wrap по словам;
- многострочный текст естественно занимает центр с небольшим визуальным сдвигом вверх;
- если не помещается — ellipsis;
- хороший контраст текста.

### Song color
- у каждой созданной песни persistent color;
- допустимо автоматическое стартовое назначение из спокойной приглушённой палитры;
- пользователь может изменить цвет в WORK AREA;
- цвет сохраняется в общем state.

### Selected / Playing
Selected pad: существующая оранжевая selection indication/border.

Playing pad:
- сохраняет свой цвет;
- становится чуть ярче;
- мягко пульсирует;
- после STOP возвращается к обычной яркости.

Selected+Playing: colored background пульсирует, orange selection border остаётся виден.

GRID и Timeline используют общий язык: `playing = slightly brighter + soft pulse`.

## Остальное сохранить
- multi-selection Timeline blocks;
- Selection != Playback != Loop;
- 64-step limit;
- INSERT/REPLACE;
- ripple editing;
- общий Live Creator state;
- UNO Pro Advanced visual theme;
- custom/themed controls вместо стандартных светлых Tk/Windows;
- `core / ui / controllers / devices`;
- controller profiles не зашивать в GRID;
- STORE/0x28 locked;
- не придумывать SysEx/CC/Note;
- software test != HARDWARE PASS.

## Acceptance checklist
1. Timeline одновременно показывает 01–32 и 33–64.
2. 32 одинаковых slots реально помещаются в строку.
3. EMPTY занимает точное число slots.
4. Block через 32/33 остаётся одним логическим block.
5. Тонкая slot grid читается и не мешает.
6. Blocks компактнее, часть имени читаема.
7. Moving playhead отсутствует.
8. Playing block мягко пульсирует.
9. White MOVE arrows отсутствуют.
10. Drag/resize/ripple/EMPTY не сломаны.
11. DEL и Right Click → Delete работают.
12. LOCAL PRESETS имеют отдельную нумерацию.
13. Drag preset → Timeline имеет ghost/target preview.
14. INSERT и REPLACE различимы до drop.
15. Pads квадратные.
16. Empty pad = только номер.
17. Filled pad = только song name.
18. Song name корректно переносится.
19. Song color выбирается и сохраняется.
20. Playing pad ярче и мягко пульсирует.
21. Selected+Playing состояния различимы.
22. WORK AREA не показывает block-info.
23. PLAY наверху.
24. PLAY DELAY label+dropdown в одной строке.
25. NAME label над широким input.
26. TEMPO label+узкий 3-digit input в одной строке.
27. STATUS/READY отсутствует.
28. PLAY/STOP больше не «отскакивает».
29. Space transport работает.
30. Клик другого pad во время playback не прерывает текущую песню.
31. Общий state сохраняется.
32. main/project_unified не затронуты.
33. Неподтверждённых hardware/MIDI функций нет.

## После реализации
Выполнить software/regression checks и собрать следующую standalone версию. В отчёте: изменённые файлы, реализованное/исправленное, оставшиеся заглушки, результаты проверок, точный путь к сборке и commit hash (если создан). Не заявлять HARDWARE PASS без реального hardware test. Не добавлять функции вне ТЗ без согласования.
