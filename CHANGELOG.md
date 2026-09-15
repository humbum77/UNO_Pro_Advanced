# Changelog

## 0.10.0-alpha — 2026-09-15

- Integrated live-creator e2b0a97 into main 51906bc; embedded LIVE page replaces legacy SONG/LIVE switch.
- Song LENGTH 1–64 clips playback/nominal timing and statistics without deleting timeline data; 4px rounded blocks.
- Preserved markers, clipboard, ripple, 32/33 wrap, selection/playback isolation and natural-entry/exit Loop.
- Added full-sequence Dupl (including decoded automation), disabled beyond 32 or with opaque native events.
- Replaced generic automation lanes with 22 parameter lines and existing multi-column picker; parameter metadata/scales, unknowns preserved.
- Native automation container reader at offsets 494/496; 495 opaque, entries remain raw. No inferred IDs/writer/MAX=17.
- Confirmed packed Sequence Length replaces last-active-step estimation.
- Global Dark/Light semantic palette, primary/secondary swap, invariant green PLAY/red REC, dark song pads.
- Toolbar Settings gear / Theme icon, retained scale/keyboard grouping; removed preset-row tag circles without deleting tag data.
- Service storage moved to %LOCALAPPDATA%\UnoLive, legacy settings/metadata read-only fallback.
- Existing STORE/0x28, protocol modules and Fill method unchanged; no new device commands.

See integration report for tests and explicit PARTIAL/UNVERIFIED items.
