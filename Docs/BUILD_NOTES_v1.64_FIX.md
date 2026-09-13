# Build Notes v1.64 FIX

Date: 2026-09-12

Hotfix based on v1.64. No protocol write behavior was unlocked.

## GUI fixes
- Scale popup is anchored to the actual scaled `⛶` top-bar button rather than a hard-coded screen position.
- Opening the drop-down keyboard no longer shrinks the whole SYNTH/SEQUENCER UI. The selected window preset keeps the main 1600x1000 design scale and adds vertical room for the keyboard.
- Keyboard key rendering now has straight top corners and only small rounded lower corners.
- Pitch Bend animation now uses the same filled-strip visual language as MOD.
- OSC1 fader spacing now uses the same pitch as OSC2/OSC3.
- FILTER vertical-fader labels have a dedicated gap above the tracks.
- LFO RATE/FADE IN faders were restored to a longer usable height with matching top/bottom spacing and label clearance.

## Preserved behavior
- UI scale presets remain 100% / 125% / 150%.
- Internal design geometry remains 1600x1000.
- STORE / SysEx 0x28 remains locked.
- v1.64 0x29 hardware sequence reader and MIDI clock work are unchanged by this hotfix.
