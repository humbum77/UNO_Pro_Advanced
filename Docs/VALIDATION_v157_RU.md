# VALIDATION v1.57 — 2026-09-10

1. Baseline: real UNO Pro Advanced v1.55 archive.
2. Python compile checks: PASS.
3. Import app.py: PASS.
4. Headless launch/draw: SYNTH / ARP + SEQUENCER / SONG / LIBRARY / SETTINGS — PASS.
5. LOCAL binary sequence decode regression:
   - test1: Step 1 C4 / velocity 42 — PASS.
   - test2: Step 1 C#4 / velocity 37 — PASS.
   - test3: Step 1 C#4 + Step 2 C4 — PASS.
   - test4: Step 2 C4 — PASS.
6. LOCAL binary .unosyp -> Preset.sequence -> ARP + SEQUENCER GUI model path: PASS headlessly.
7. Settings: first-run Preview ON, dirty APPLY path, no SAVE SETTINGS button — PASS static/headless.
8. Main selector: no HARDWARE/ prefix — PASS static.
9. Tags submenu / tag gap / UP-DOWN / horizontal scrollbar / drag ghost / SONG tree — PASS static + page draw smoke.
10. Filter ENV +64 full positive visual scaling and Attack/Decay/Sustain/Release marker math — PASS deterministic/headless.
11. STORE/0x28 lock preserved — PASS static.
12. Hardware Voice Mode MONO/LEGATO/PARA receive: NOT VERIFIED / confirmed mapping absent from current evidence.
13. Hardware Mod Matrix Source/Destination receive: NOT VERIFIED / confirmed mapping absent from current evidence.
14. 0x36 LOCAL binary synth preview: TEST / NOT HARDWARE-CONFIRMED.
15. No hardware PASS is claimed by this validation.
