# UNO2.2 UI / Library implementation report — 2026-09-22

Base: `UNO Pro Advanced v0.9.7-beta2-STORE-LIBRARY-SIMPLE`.

Implemented:

- settings and rotating editor logs use `%LOCALAPPDATA%\UnoLive` only;
- user `.unosyp` presets remain in the existing Documents preset library;
- vertical faders use upper vertical labels and persistent values below shortened tracks;
- ADSR uses horizontal A/D/S/R labels and persistent values;
- ordinary slider popups are disabled; modulation-matrix tooltips remain;
- oscillator FINE controls are replaced by LEVEL 1/2/3 controls;
- TUNE combines fine cents around zero with coarse semitone values;
- level faders were removed from NOISE without reflowing its remaining controls;
- the UI-scale toolbar button was removed;
- ARP + SEQUENCER now shows TEMPO and STEPS on one row, with STEPS as a dropdown;
- repeated clicks close the same STEPS/LENGTH selector;
- LOCAL preset viewport is sized for exactly three 210-pixel columns;
- the right panel receives the remaining width and uses matching column spacing;
- Library file scanning is cached until an explicit invalidation, reducing page and operation latency;
- horizontal scrollbar hit areas and direct dragging remain available, with wheel scrolling over both panels;
- `Move >` stores the selected LOCAL preset into the selected UNO slot;
- `< Move` is present and intentionally disabled because its operation is undefined by the specification;
- the corrected fix13-compatible sequence-note alignment remains included.
- `.unosyp` editor JSON presets are auto-detected before binary parsing; the
  `FAKE 808` regression fixture decodes as 62 steps with 16 active steps.

Validation:

- Python compilation passed;
- focused storage, layout, envelope, Live Creator, Store and automation tests passed;
- 22 available `.unosyp` samples match the fix13 note/velocity/extra decoding;
- ZIP CRC and SHA-256 manifest validation passed during packaging.
