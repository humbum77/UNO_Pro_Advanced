# UNO2.2 Sequencer redesign — implementation status (2026-09-25)

Base: `UNO2.2_LIVE_MIDI_STOP_FIX`.

## Implemented
- Removed separate ARPEGGIATOR left rail; ARP controls grouped into SEQUENCE SETTINGS.
- Removed legacy Gate / ACC / Velocity / Length / Tie strip.
- Removed FILL / DUPLICATE buttons.
- Piano-roll keeps the former step width as 100% baseline.
- Box note selection, Ctrl+D duplicate with copied notes retaining selection, Left/Right group movement.
- Note Length by dragging note right edge.
- Note context menu: Gate ON/OFF, Accent ON/OFF, Legato ON/OFF, Delete.
- Horizontal anchored piano-roll zoom, 100–400%, 25% increments.
- Automation panel collapsible; collapsed height is returned to piano-roll.
- VELOCITY added to Automation.
- Shared sequence Gate and Accent values added to SEQUENCE SETTINGS. Step context toggles only enable/disable the global value.
- Native writer now writes the confirmed shared Gate/Accent state fields at file offsets 209/210 and 212.

## Hardware-format boundary
The existing decoder confirms shared Gate/Accent values and per-step Gate/Accent/Tie maps. The UI now respects that model. Per-step map writing and note/Length writing are not claimed as newly verified here; they must not be invented without confirmed native encoding/round-trip evidence.

## Verification
- Python compilation passes for modified modules.
- Gate/Accent encode→decode round-trip: 44/44 combinations passed (Gate 0..10 × Accent 0/1/64/127).
- Focused sequencer/UI tests: 12 passed, 4 skipped, 4 subtests passed.
- Automation metadata test expectation updated from 22 to 23 parameters because VELOCITY is now intentionally included.
