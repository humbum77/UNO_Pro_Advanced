# UNO Pro Advanced v1.62

## UI scaling
- Design base changed to 1600×900 (16:9).
- 100% UI scale is now exactly 1600×900.
- Scale presets: 50% = 800×450, 75% = 1200×675, 100% = 1600×900, 125% = 2000×1125, 150% = 2400×1350.
- Added 75% to Settings → UI SCALE.
- Scale calculation remains proportional: `min(window_width / 1600, window_height / 900)`.

## Cumulative changes
- Includes the v1.61 codebase and the read-only hardware sequencer 0x29 integration prepared after v1.61.
- STORE/write behavior remains locked; no permanent hardware write was added.
