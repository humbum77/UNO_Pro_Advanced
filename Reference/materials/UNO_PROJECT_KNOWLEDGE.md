# UNO Pro Advanced — единый контекст проекта

Актуализировано: 2026-09-11. Этот документ предназначен для добавления в источники проекта ChatGPT **UNO**.

## 1. Правила достоверности

- **CONFIRMED / HARDWARE PASS** — подтверждено физическим UNO Synth Pro или контролируемым capture.
- **IMPLEMENTED** — реализовано в коде, но это не всегда означает аппаратную проверку.
- **TEST / PROVISIONAL** — экспериментально или требует более длительной проверки.
- **RESEARCH / NOT CONFIRMED** — гипотеза; нельзя использовать для опасных записей.
- Более свежее прямое подтверждение пользователя имеет приоритет над старыми документами.
- Не приписывать неизвестным полям семантику и не использовать «ближайшие» значения вместо точного декода.

## 2. Последние обязательные пользовательские уточнения

- **Voice Mode работает в текущей сборке.** Считать закрытым и не возвращать в список дефектов без новой регрессии. Старые записи `Voice Mode FAIL` устарели.
- На физическом UNO параметры **Velocity** и **Length** не редактируются пользователем. Не предлагать аппаратные тесты с их ручным изменением.
- **TIE** — только бинарный параметр `ON/OFF`; других значений нет.
- Неосвещённый шаг означает, что в нём сейчас нет записанных данных. В выбранный пустой шаг можно записать automation/параметр (например Cutoff); после появления данных шаг становится активным/светится. Активность шага не равна только наличию ноты.
- **Matrix Fade In** работает в текущем использовании. Не считать дефектом и не переделывать по неподтверждённой packed-state шкале.
- **ARP RATE не является аппаратным параметром UNO Synth Pro.** Не добавлять его обратно и не назначать ему CC/SysEx.

## 3. Текущее состояние приложения

- Последняя документированная собранная база: v1.58 test build candidate.
- В `app.py` присутствуют рабочие изменения v1.59, однако отдельная сборка v1.59 документами не подтверждена.
- Сборку создавать только после прямой команды пользователя «Сделай сборку» или равнозначной.
- Каждая новая сборка должна быть кумулятивной: сверить разговоры после предыдущей сборки, `FIXED_CHANGES.md`, `UNO_PROJECT_TASKS.md` и `PROJECT_STATE.md`.
- Архивную/reference v1.29 не изменять без прямого запроса.

## 4. Подтверждённая синхронизация аппаратных пресетов

Подтверждённый цикл:

1. UNO выдаёт Program Change.
2. Затем приходит SysEx-уведомление `0x32`.
3. Editor запрашивает текущее состояние: `F0 00 21 1A 02 03 37 00 00 F7`.
4. UNO отвечает пакетом `0x37` общей длиной **309 байт**.
5. Примерно через 0,5 с Editor запрашивает имя через `0x24`.
6. UNO возвращает 43-байтный `0x24` с адресом слота и ASCII-именем.

Работают имена и двусторонняя синхронизация слотов `001–256`.

Запрос имени слота N, где `n=N-1`:

```text
F0 00 21 1A 02 03 24 01 <bank> <program> F7
bank = n // 128
program = n % 128
```

## 5. `0x37` — current state

- Запрос: `F0 00 21 1A 02 03 37 00 00 F7`.
- Ответ начинается: `F0 00 21 1A 02 03 00 37 00 00`.
- Общая длина изученного ответа: 309 байт.
- Полной семантики всех 309 байт пока нет.
- Последовательный hardware sweep: 87 CC × 128 значений = **11 136 измерений**.
- Наблюдаемые сигнатуры найдены для 83 из 87 CC.
- `CC7`, `CC110`, `CC111`, `CC112` не дали изменения в том контексте; это не доказывает отсутствие параметров в состоянии.
- Runtime-декодер применяет только точные observed LUT-сигнатуры. Nearest/guess fallback запрещён.
- Режимно-зависимые Delay/Reverb поля требуют осторожности из-за последовательного характера sweep.

Подтверждённые поля секвенсора в current-state:

```text
Direction = data[219] & 0x30
0x00 Forward
0x10 Backward
0x20 Back'n'Forth

gate_raw = (data[221] << 7) | (data[220] & 0x60)
gate = gate_raw / 32

TIE = bool(data[220] & 0x10)
ACCENT = data[223] & 0x7F
```

Байты 219/220/221/223 композитные: при записи необходимо маскирование с сохранением остальных битов. Нельзя переносить эти offsets на flash-структуру шагов.

## 6. Подтверждённые MIDI/FX значения

```text
Filter 1 Mode CC30: 0/25/50/75/100
Filter 2 Mode CC37: 0/20/40/60/80/100
MOD Type CC95: Chorus=0, Phaser=42, Flanger=84
Chorus Mode CC98: SYNTH1=0, SYNTH2=42, STRINGS=84
Phaser Color CC96: COLOR1=0, COLOR2=127
Delay Type CC100: Mono=0, Stereo=25, Doubler=50, Ping Pong=75, LCR=100
Reverb Type CC107: Hall=0, Plate=32, Reverse=64, Spring=96
LFO1 Fade In CC46; LFO2 Fade In CC50
```

MIDI Clock: 24 PPQN; проект использует 6 clock pulses на один 16-й шаг. Start=`FA`, Stop=`FC`.

## 7. ARP и Mod Matrix

- `0x3E` receive для ARP Direction/Range/Pattern реализован и аппаратно проверен.
- `0x3C 00 02` send для 16-step ARP Pattern реализован; Pattern работает в обе стороны.
- ARP Range пишет native `1..4`.
- ARP ON/OFF sync оставался без подтверждённой карты в старой документации.
- Matrix Source/Destination/Amount аппаратно отражаются в GUI.
- Packed-state формула Matrix:

```text
Destination: bits 5..10
Fade raw: bits 11..20
Amount raw: bits 21..28
Source: current bits 29..31 + next chunk bits 0..4
```

- Factory slot59 cross-check воспроизводил routes `(27,1,14)`, `(41,2,31)`, `(32,17,10)`, `(29,0,18)`.
- 10-bit `fade_raw` read-side scale не декодирована независимо. Не подменять рабочий Matrix Fade In догадкой.

## 8. `.unosyp` и секвенсор

- Поддержанный бинарный вариант: **1081 байт**, header `25 01 00 00`.
- Read-only decoder: 4 pages × 16 steps = 64 шага; 10 байт на запись; до 3 голосов.
- Извлекаются note, per-note velocity, extra и `control_raw`; неизвестные поля сохраняются без выдуманной семантики.
- 1084-byte `test5` обрабатывается безопасно как state-only; sequence decode для него не заявлять.
- LOCAL binary state bytes `0..296` преобразуются в synth/current-state представление и проходят через точный LUT.
- Hardware `0x37` не содержит подтверждённого полного массива 64 шагов. Переключение на аппаратный пресет очищает устаревшую LOCAL sequence и помечает источник как `HARDWARE_STATE_ONLY`.
- Полное чтение 64 аппаратных шагов остаётся отдельной задачей.

Flash-структура с сильной структурной поддержкой:

```text
Preset slot size: 0x1000 (4096 bytes)
Studied preset 1 address: 0x09F000
Sequence block within slot: 0x101..0x380
64 records × 10 bytes
step_offset = 0x101 + step_index * 10

+0 control/flags (точные биты не подтверждены)
+1 note1; +2 velocity1; +3 extra1
+4 note2; +5 velocity2; +6 extra2
+7 note3; +8 velocity3; +9 extra3
FF в note field = пустой voice slot
```

`+3/+6/+9` — кандидаты duration/length, но это не подтверждённая семантика. `+0` выглядит как 6-bit packed field; точные Gate/Tie/Accent биты во flash не установлены.

## 9. Firmware / updater / DFU

- Updater использует USB DFU/DfuSe для firmware/preset payload; MIDI/SysEx служит для связи/входа в bootloader.
- Из статического анализа известна команда bootloader:

```text
F0 00 21 1A 02 01 11 00 42 4F 4F 54 20 55 4E 4F 00 F7
```

- Она означает `BOOT UNO\0` и **не должна отправляться при обычном тестировании Editor**.
- Preset DFU: сильная карта 4096-байтных слотов, 128 заполненных factory slots; изученный preset 1 начинается с `0x09F000`.
- Точная write-команда updater для `USP_Presets.dfu`, адресный UPLOAD через `dfu-util 0.8` и read-функция firmware/updater должны считаться незавершёнными, пока их точные результаты не внесены отдельным capture/документом. Нельзя дополнять их по памяти.

## 10. STORE и опасные команды

- `0x28` связан с bulk preset write/store; наблюдался 304-byte frame, но преобразование payload не доказано.
- STORE/`0x28` постоянно заблокирован. Runtime не должен содержать конструктор `0x28`, пока формат не подтверждён.
- `0x36` — только TEST/current-buffer preview, не считать аппаратно подтверждённым без нового прямого результата.
- Bootloader SysEx запрещён в обычных тестах.
- Не использовать команды UNO Drum `0x33–0x37` как доказательство протокола UNO Synth Pro без отдельного capture.

## 11. Реализованное и сохраняемое поведение

- GUI-sync из `0x37` без MIDI echo.
- LOCAL JSON preview через подтверждённые CC, без Program Change и STORE.
- LOCAL/ALL Library, рекурсивное flattening `.unosyp`, исключение songs.
- Favorite + 7 цветных меток, drag/drop, metadata ordering.
- Envelope point editing и отдельный live marker.
- В v1.59 working source: nonlinear graph-only ADSR mapping; AD horizontal, DS horizontal+vertical, SR vertical, R horizontal; MIDI/raw значения не меняются.
- Sequencer Piano Roll: один клик выбирает ноту, двойной удаляет, rectangle показывает сохранённый length.
- CLEAR использует тематическое подтверждение `ДА/НЕТ`.
- LFO Fade In default OFF.
- Matrix dropdown перехватывает wheel, не прокручивая Matrix под ним.
- Session restore сохраняет LOCAL/HARDWARE выбор без передачи MIDI при старте.
- Matrix LFO→Filter Cutoff визуально анимирует кривую фильтра; это GUI behavior, не аппаратная валидация протокола.
- Хранилище использует Windows Known Folder Documents; запись settings атомарная (`mkstemp` + replace).
- MIDI receive: ~10 ms queue/coalescing для CC; Clock/Note/SysEx не коалесцируются.

## 12. Актуальные открытые задачи

### P0 — протокол и безопасность

- Найти безопасное полное чтение аппаратной 64-step sequence.
- Полностью декодировать `0x28` до любого снятия STORE lock.
- Подтвердить или окончательно отклонить `0x36` current-buffer load.
- Документировать точные результаты анализа `USP_FW_Main.dfu`, `USP_Presets.dfu`, updater и `dfu-util 0.8` address UPLOAD.

### P1 — синхронизация

- Найти подтверждённую ARP ON/OFF sync.
- Найти подтверждённую SEQ ON/OFF sync; учитывать, что hardware state меняется кнопками SEQ и PLAY.
- Продолжить длительную проверку прежнего LOCAL/HARDWARE/LOCAL stall.

### P2 — качество проекта

- Обновить `PROJECT_STATE.md` под фактическое состояние v1.59 working source.
- Создать `VALIDATION_v159_RU.md` и провести пользовательскую/аппаратную проверку.
- Централизовать enum/raw tables в `protocol_map.py`.
- Заменить `_save_uno_drop` delay 180 ms на ожидание конкретного state response с timeout.
- Вынести `sequence_origin` в enum.
- Рефакторить монолитный `app.py` только после стабилизации P0.

## 13. Источники, использованные при консолидации

- `PROJECT_STATE.md`
- `FIXED_CHANGES.md`
- `UNO_PROJECT_TASKS.md`
- `HARDWARE_TEST_RESULTS.md`
- `SYSEX_PROTOCOL.md`
- `MIDI_REFERENCE.md`
- `STATE_0x37_MAP.md`
- `PRESET_FLASH_FORMAT.md`
- `UPDATER_DFU_RESEARCH.md`
- `RESEARCH_INDEX.md`
- `UNO_TEST_DATA_ALL.md`
- `Анализ проекта UNO Pro Advanced.docx`
- Последние прямые уточнения пользователя в ветках UNO.

