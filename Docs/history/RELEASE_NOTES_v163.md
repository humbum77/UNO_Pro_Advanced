# UNO Pro Advanced v1.63

## UI scale
- UI scale presets are now only: 100% = 1200×675, 125% = 1440×810, 150% = 1600×900, plus FULLSCREEN.
- 125% / 1440×810 is the preferred working size.
- Design coordinate base remains 1600×900. Esc exits fullscreen to 125%.

## Hardware sequence read
- Read-only 0x29 sequence transaction remains page 0 -> 4.
- Fix candidate for the user-reported "preset 1 sequence on every hardware preset": 0x29 requests now carry the selected slot as two 7-bit bank/program bytes, matching the existing preset-address convention. Preset 1 remains 00 00; preset 2 becomes 00 01; preset 129 becomes 01 00. This non-001 addressing still requires direct hardware validation.
- STORE / 0x28 remains locked.

## Sequencer UI
- Removed the `SEQUENCE SOURCE: ...` text after the SEQUENCER heading.
- FILL now flashes its active styling after click so the action has visible feedback.
- Automation pencil stores/displays one value per parameter per step. Different automation lanes/parameters may each have a value on the same step; four sub-step values for one parameter are no longer created/displayed.

## Library
- Clicking or arrowing through Library only changes highlight. Enter performs LOCAL load/preview or hardware preset selection/read. Top-bar preset selection behavior is unchanged.
- Arrow navigation follows the visual grid: Up/Down move vertically; Left/Right move between columns.
- LOCAL panel is narrowed for three visible preset columns; right panel is widened for two columns, with a 28 px inter-panel gap and explicit inner frame.
- ALL filtering caches preset metadata for the redraw instead of repeatedly rereading it during sorting/filtering/rendering.

## Song
- Folder rows are no longer highlighted as selected in the SONG explorer; only preset files receive selection highlighting.
