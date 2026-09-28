# VALIDATION v1.53

## Автоматические проверки
- Python compile: PASS.
- Импорт приложения: PASS.
- Headless Tk launch/redraw: PASS.
- MODULATION third-level UI: CHORUS = SYNTH1/SYNTH2/STRINGS; PHASER = COLOR1/COLOR2; ordinal 1:1 preserved.
- Envelope: point-only edit hitboxes; points hidden until hover/drag; separate visual live marker.
- LOCAL Library: only first-level folders are exposed; selected folder scans *.unosyp recursively; songs excluded.
- STORE remains locked. Frozen FX raw tables unchanged.

## Главный аппаратный тест
1. На UNO выбрать пресеты/состояния CHORUS с SYNTH1, SYNTH2, STRINGS и смотреть, какая кнопка активируется в GUI.
2. Повторить для PHASER COLOR1/COLOR2.
3. Менять пресет с UNO и из Editor; проверить, что MODULATION type и third-level button follow hardware state.
4. Если CHORUS работает, а PHASER нет — отдельно снять 0x37 для COLOR1/COLOR2; не угадывать mapping.
