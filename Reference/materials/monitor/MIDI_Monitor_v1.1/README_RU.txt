UNO Synth Pro MIDI Monitor v1.1 State Read

Что добавлено:
- кнопка READ STATE 0x37;
- она отправляет только подтвержденный запрос текущего состояния:
  F0 00 21 1A 02 03 37 00 00 F7
- ответ UNO 309 байт попадает в лог как UNO state 309B;
- монитор работает как прокси между UNO и официальным Editor через UNO_TAP / UNO_RETURN;
- MIDI Clock и Active Sense по умолчанию не пишутся.

Подключение:
UNO IN                = UNO Synth Pro
UNO OUT               = UNO Synth Pro
EDITOR OUT / TAP IN   = UNO_TAP
EDITOR IN / RETURN OUT= UNO_RETURN

В официальном UNO Synth Pro Editor выбери:
MIDI OUT = UNO_TAP
MIDI IN  = UNO_RETURN

Тест:
1. Запусти монитор и нажми START.
2. Открой официальный Editor через UNO_TAP / UNO_RETURN.
3. Выбери чистый пресет и не меняй его.
4. Нажми READ STATE 0x37 — это baseline.
5. Измени только один параметр, например OSC 1 WAVE.
6. Снова нажми READ STATE 0x37.
7. Нажми Save и пришли TXT.

Важно: монитор ничего не STORE и не пишет во flash. READ STATE только читает текущее состояние.
