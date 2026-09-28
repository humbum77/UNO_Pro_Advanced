Current: **v0.9.2-beta**. [Requested rollback](RELEASE_NOTES_v0.9.2-beta.md) supersedes the historical notes below.

# Current release: v0.9.0-beta

The post-FIX2 changes are implemented in this build. See [release notes](RELEASE_NOTES_v0.9.0-beta.md) and [validation](VALIDATION_v0.9.0-beta.md) for current status. Earlier statements below are historical and are superseded by these release notes where they differ. Hardware limitations remain open.

---

# GUI_SPEC.md

Frozen essentials: top navigation SYNTH | ARP + SEQUENCER | SONG | LIBRARY; final right side SAVE | STORE | SETTINGS; READ is service/dev only; no LOAD/RESTORE topbar. Stable Canvas scaling/keyboard overlay architecture, numeric entry, popups, ENV hit zones, RANDOM and frozen FX UI must not regress. LFO labels use exact `FADE IN`; zero is OFF.

## Library / preset selector — v1.51 fixed
- HARDWARE remains a single continuous 001–256 list in Library; no page UI.
- Hardware names, when read from UNO via confirmed `0x24`, are displayed beside slot numbers and in the main preset selector/tree.
- LOCAL folder disclosure triangles are visually larger; the existing full-row folder hit area remains active, making folder navigation easier to click.

## Library / preset selector — v1.54
- LOCAL preset left click: select + immediate editor-native preview; no context menu.
- LOCAL preset right click: dark context menu with `★` then seven smooth circular color tags in one row; below it Rename / Copy / Cut / Paste / Delete. No Load command and no Tags submenu.
- Preset rows have no leading preset/file icon. Folder/tree icons remain.
- Add Folder has no toolbar icon; New folder lives in folder context menu and uses inline naming.
- Right toolbar ends with `Uno` then a small gap then Receive / Send; these controls remain position-stable.
- Main LOCAL preset selector label is only the preset name, never `folder / preset`.
- Main preset source menu uses exact label `UnoSynth` for the device source.
- Context menus and preset selector menus use the dark application palette.
- Topbar READ is removed.


## v1.55 — LOCAL binary preview test (2026-09-10)
- TEST/NOT YET HARDWARE-CONFIRMED: official UNO Synth Pro binary `.unosyp` matching header `25 01 00 00` and expected payload length may be previewed using externally documented current-buffer SysEx `0x36`; no Program Change, STORE or `0x28` is sent.
- After `0x36`, editor requests current state `0x37` so confirmed decoder fields can rebuild GUI from the UNO response.
- SAFETY: malformed/unexpected binary files are rejected rather than transmitted. This `0x36` path must remain TEST until reproduced on the user's real UNO.
- UI: preset context menu Favorite star is always yellow; seven smaller anti-aliased circular tags are shown directly in one row. Library tag dots use anti-aliased rendering.


## ADSR envelope graph — fixed visual target 2026-09-11
1. Applies identically to FILTER ENV and AMP ENV.
2. A/D/R short-time visualization must become visibly responsive from approximately 20 ms equivalent; the current approximately 75 ms visual threshold is too coarse.
3. Sustain is represented by a horizontal S→R segment once S is approximately 3% or greater. The segment height follows S. Near zero Sustain, the segment may visually collapse to the S entry point.
4. A/D/R time-to-horizontal-distance mapping is nonlinear/log-like so short values remain distinguishable without making long values exceed the graph.
5. The ADSR curve remains an editor visualization of existing parameters. No MIDI/raw parameter range or hardware protocol mapping is changed by this GUI rule.
6. The live envelope-position marker remains separate from editable envelope geometry and traverses Attack → Decay → Sustain hold → Release along the revised curve.

## v1.59 GUI interaction additions — fixed/implemented working source 2026-09-11
1. ADSR editing: AD point moves left/right only; DS point moves left/right and up/down; SR sustain segment is draggable vertically; R point moves left/right only.
2. LIBRARY HARDWARE list is column-based with horizontal scrolling. LOCAL and HARDWARE panels accept mouse-wheel scrolling over the panel under the cursor.
3. LOCAL preset names must be clipped to the visible column width and never draw into neighboring fields.
4. LIBRARY arrow-key navigation remains available in LOCAL and HARDWARE panels.
5. SONG preset selection uses a simple folder/preset tree. Single click on a folder toggles open/closed; Up/Down/Left/Right keyboard navigation remains available.
6. Piano Roll: one click on an existing note selects it; double-click deletes it; selected note has a visible outline; note width reflects stored LENGTH.
7. Sequencer CLEAR opens an in-theme confirmation window with `ДА` and `НЕТ`.
8. Matrix SOURCE/DESTINATION dropdowns consume mouse-wheel input while open. Their initial scroll position may be anywhere appropriate (current value vicinity is acceptable); Matrix scrolling resumes only after the dropdown closes.
9. LFO Fade In default display/state is OFF.
10. Last selected LOCAL/HARDWARE preset is restored at startup without an automatic hardware preset-change transmission caused solely by session restore.

## v1.64 GUI delta — 2026-09-12
- Reference internal geometry restored to 1600×1000.
- Window presets: 1200×675, 1440×810, 1600×900; Windows maximize/resize enabled.
- Top-bar scale menu `⛶`; Settings no longer contains UI Scale.
- Tabs: SYNTH / ARP + SEQUENCER / LIBRARY / SONG.
- OSC layout: OSC1|NOISE / OSC2|OSC3; LEVEL 1/2/3 consolidated into NOISE with NOISE level.
- Keyboard: borderless, no heading, 3 octaves, layout-integrated (not overlay), stacked octave arrows, paired Pitch/Mod strips, PB Range 2/4/6/8/12/24.
- Settings: left MIDI controls with MIDI Interface below SYNC; right ABOUT.
- Sequencer automation scale labels: 100/50/0/-50/-100.
- Library keyboard horizontal movement keeps selected item in viewport.

## v1.64 FIX GUI delta — 2026-09-12
- Scale popup: directly below the scaled `⛶` button.
- Keyboard panel must not reduce the scale of the main 1600x1000 SYNTH/SEQ layout; opening it adds the required vertical area.
- Piano keys: top edge/corners straight; only lower corners slightly rounded.
- Pitch Bend and MOD share the same filled-strip animation language.
- OSC1 fader spacing equals OSC2/OSC3 spacing.
- FILTER/LFO vertical labels must not touch their fader tracks.
- LFO RATE/FADE IN tracks use full available vertical height with consistent top/bottom margins.

## v1.64 FIX2 scaling / sequencer UI
- Canonical design area: 1600x1000.
- Scale presets: 100%=1200x750, 125%=1440x900, 150%=1600x1000.
- Window cannot be freely resized by dragging edges/corners.
- Drop-down keyboard extends the window vertically without reducing the main design scale.
- Keyboard octave arrows have a numeric current-shift indicator on their right.
- Sequencer playhead is a thin low-contrast vertical line, not a filled/highlighted column.
- Piano roll auto-fits only after sequence load. Wide note spreads use the densest visible range; notes beyond the current range get subtle up/down indicators.
- MIDI CLOCK selector: Off / MIDI MASTER only.
