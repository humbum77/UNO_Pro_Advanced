# VALIDATION v1.55

Date: 2026-09-10

- Python compile: PASS (`app.py`, `storage.py`, `data_model.py`, `protocol_map.py`, `midi_engine.py`, `state_decoder.py`, `main.py`).
- Headless Tk Library launch: PASS; title `UNO Pro Advanced v1.55`.
- Binary `.unosyp` preview envelope unit test: PASS for strict test shape (`25 01 00 00`, payload bytes 4..0x128, all 7-bit); malformed header rejected.
- Generated test SysEx is exactly `F0 00 21 1A 02 03 36 00 60 + 0x125 payload bytes + F7` (303 bytes total).
- v1.55 binary preview path does not use Program Change, STORE or `0x28`; it schedules a current-state `0x37` read after preview send.
- UI code contains seven tag colors in one inline context row, smaller anti-aliased circles, and an always-yellow Favorite star.
- IMPORTANT: command `0x36` remains TEST / NOT YET HARDWARE-CONFIRMED in this project. Real UNO validation is required before promoting it to CONFIRMED.
