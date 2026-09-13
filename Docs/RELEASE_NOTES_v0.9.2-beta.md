# v0.9.2-beta — requested rollback

- Restored FIX2 scale presets 100/125/150 and topbar ⛶. First launch after this update defaults to 100% (1200 × 750); subsequent user choices persist. FIX2 fixed window/preset sizing is restored.
- Restored FIX2 FILL size and explanatory text below it. Removed SAVE/SAVE AS and the working-file indicator from the sequencer panel.
- Topbar retains SAVE and SAVE AS. SAVE uses the FIX2 name dialog and unique numbered copies in the default preset folder. SAVE AS exports a copy to a chosen path, with overwrite confirmation and binary-file protection.
- Removed the project-folder/current-working-file/dirty-state workflow and its Save / Don't Save / Cancel prompts. Browsing or closing no longer prompts for unsaved changes.
- Retained the other beta fader and LIVE drag changes. FIX2 MIDI protocol, clock, thin playhead, autofit, octave indicator and locked STORE are retained. SEQ ON/OFF and preset 2 0x29 limitation remain unchanged.

Validation: 7 offline tests pass (scales/migration, button placement, legacy SAVE/export, no browsing prompts, LIVE drag, protocol note decode); all Python sources compile. Native Tk and hardware validation remain unperformed in this environment. Older test_beta.py contains superseded workflow tests; use test_v092.py for this release.
