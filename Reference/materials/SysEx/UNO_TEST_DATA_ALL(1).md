# UNO Synth Pro Editor — consolidated test data

Generated from preserved hardware MIDI/SysEx test captures. This file is intended as the single research reference for future protocol/flash analysis.



# OFFICIAL MIDI CHART — QUICK REFERENCE

Source: IK Multimedia UNO Synth PRO MIDI Implementation Chart v1.0.0. This section is the canonical quick lookup for standard MIDI CC. Official-chart mappings are kept separate from reverse-engineered SysEx/flash findings below.

## Core / OSC / FILTER / LFO / ENV

| CC | UNO function | Status |
|---:|---|---|
| 0 | Bank Select MSB (2 banks) | OFFICIAL |
| 1 | Modulation Wheel | OFFICIAL |
| 5 | Glide Time | OFFICIAL |
| 7 | VCA Level | OFFICIAL |
| 9 | Swing Amount | OFFICIAL |
| 12 | OSC 1 Wave | OFFICIAL |
| 13 | OSC 2 Wave | OFFICIAL |
| 14 | OSC 3 Wave | OFFICIAL |
| 15 | OSC 1 Tune (±12 semitones) | OFFICIAL |
| 16 | OSC 2 Tune (±12 semitones) | OFFICIAL |
| 17 | OSC 3 Tune (±12 semitones) | OFFICIAL |
| 18 | OSC 1 Level | OFFICIAL |
| 19 | OSC 2 Level | OFFICIAL |
| 20 | OSC 3 Level | OFFICIAL |
| 21 | Noise Level | OFFICIAL |
| 22 | OSC 2 Sync ON/OFF | OFFICIAL |
| 23 | OSC 3 Sync ON/OFF | OFFICIAL |
| 24 | OSC Ring ON/OFF | OFFICIAL |
| 25 | OSC 2 FM Amount | OFFICIAL |
| 26 | OSC 3 FM Amount | OFFICIAL |
| 28 | FILTER 1 Cutoff | OFFICIAL |
| 29 | FILTER 1 Resonance | OFFICIAL |
| 30 | FILTER 1 Mode | OFFICIAL |
| 31 | FILTER 1 Filter Env Amount | OFFICIAL |
| 32 | FILTER 1 Key Track Amount | OFFICIAL |
| 35 | FILTER 2 Cutoff | OFFICIAL |
| 36 | FILTER 2 Resonance | OFFICIAL |
| 37 | FILTER 2 Filter Env Amount | OFFICIAL |
| 38 | FILTER 2 Key Track Amount | OFFICIAL |
| 39 | FILTER 2 Spacing | OFFICIAL |
| 40 | FILTER Link | OFFICIAL |
| 41 | FILTER 2 Mode | OFFICIAL |
| 44 | LFO 1 Wave | OFFICIAL |
| 45 | LFO 1 Rate | OFFICIAL |
| 46 | LFO 1 Fade In | OFFICIAL |
| 47 | LFO 1 Sync | OFFICIAL |
| 48 | LFO 2 Wave | OFFICIAL |
| 49 | LFO 2 Rate | OFFICIAL |
| 50 | LFO 2 Fade In | OFFICIAL |
| 51 | LFO 2 Sync | OFFICIAL |
| 53 | FILTER ENV Attack | OFFICIAL |
| 54 | FILTER ENV Decay | OFFICIAL |
| 55 | FILTER ENV Sustain | OFFICIAL |
| 56 | FILTER ENV Release | OFFICIAL |
| 57 | FILTER ENV Loop ON/OFF | OFFICIAL |
| 58 | FILTER ENV Retrigger ON/OFF | OFFICIAL |
| 59 | AMP ENV Attack | OFFICIAL |
| 60 | AMP ENV Decay | OFFICIAL |
| 61 | AMP ENV Sustain | OFFICIAL |
| 62 | AMP ENV Release | OFFICIAL |
| 63 | AMP ENV Loop ON/OFF | OFFICIAL |

## Modulation Matrix

CC 66–81 = Matrix Slot 1–16 Amount respectively. Official chart exposes Amount only; Source/Destination/Fade In mappings are NOT established by the chart and must not be invented.

## FX

| CC | UNO function | Status |
|---:|---|---|
| 90 | Drive Amount | OFFICIAL |
| 91 | Reverb Amount | OFFICIAL |
| 92 | Delay Amount | OFFICIAL |
| 93 | Mod Amount | OFFICIAL |
| 95 | Mod Type | OFFICIAL + HW TESTED |
| 96 | Mod Intensity (Phaser Color / Flanger Feedback) | OFFICIAL |
| 97 | Mod Rate | OFFICIAL |
| 98 | Chorus Mode | OFFICIAL |
| 100 | Delay Type | OFFICIAL + HW TESTED |
| 101 | Delay Sync ON/OFF | OFFICIAL |
| 102 | Delay Time L | OFFICIAL |
| 103 | Delay Time R | OFFICIAL |
| 104 | Delay Feedback | OFFICIAL |
| 105 | Delay Filter | OFFICIAL |
| 107 | Reverb Type | OFFICIAL + HW TESTED |
| 108 | Reverb Pre-Delay | OFFICIAL |
| 109 | Reverb Time (Reverse/Spring) | OFFICIAL |
| 110 | Reverb Time LOW | OFFICIAL |
| 111 | Reverb Time MID | OFFICIAL |
| 112 | Reverb Time HIGH | OFFICIAL |
| 113 | Reverb Size | OFFICIAL |
| 114 | Reverb Filter | OFFICIAL |

## Hardware-tested discrete FX raw values

- MOD TYPE CC95: CHORUS=0, PHASER=42, FLANGER=84. CONFIRMED on hardware.
- DELAY TYPE CC100: MONO=0, STEREO=25, DOUBLER=50, PING PONG=75, LCR=100. CONFIRMED on hardware.
- REVERB TYPE CC107: HALL=0, PLATE=32, REVERSE=64, SPRING=96. CONFIRMED on hardware.

## Standard MIDI transport / notes used by the project

- Note On / Note Off: keyboard and sequencer note traffic.
- Program Change + Bank Select: preset recall/synchronization.
- MIDI Clock F8: captured from hardware; project sequencer uses 24 PPQN semantics, 6 clocks per 16th step.
- Start FA / Stop FC: transport handling in editor.

## SysEx note from official chart

Page 4 identifies System Exclusive Message Function but does not provide the proprietary byte-level command specification. Therefore the byte-level SysEx command map in this document comes from our captures/static reverse engineering and is labelled separately by confidence.

---

## Status legend
- **CONFIRMED** — directly supported by controlled hardware captures.
- **HIGH CONFIDENCE** — strong structural/statistical inference, not yet isolated by a one-variable hardware test.
- **NOT CONFIRMED** — hypothesis only; do not use for hardware writes.

## Confirmed 309-byte state dump

- Request: `F0 00 21 1A 02 03 37 00 00 F7`
- Response prefix: `F0 00 21 1A 02 03 00 37 00 00`
- Total response length: **309 bytes**.
- Notes recorded into sequencer steps do **not** appear as a simple 64-step note array in this dump.

### Sequencer Direction — CONFIRMED read mapping
`byte[219] & 0x30`
- `0x00` = Forward
- `0x10` = Backward
- `0x20` = Back'n'Forth
Other bits in byte 219 must be preserved. A real Forward capture returned raw `byte[219]=0x02`, proving the whole byte is not the direction value.

### Gate — CONFIRMED read mapping
`gate_raw = (data[221] << 7) | (data[220] & 0x60)`
`gate = gate_raw / 32`
Controlled values observed:

| Gate | byte220 relevant | byte221 | raw |
|---:|---:|---:|---:|
| 0 | 00 | 00 | 0 |
| 1 | 20 | 00 | 32 |
| 2 | 40 | 00 | 64 |
| 3 | 60 | 00 | 96 |
| 4 | 00 | 01 | 128 |
| 10 | 40 | 02 | 320 |

### Tie — CONFIRMED read mapping
`TIE = bool(data[220] & 0x10)`
Example at Gate=10: OFF gives byte220 `0x40`; ON gives `0x50`. Gate/Tie share byte220, so writes must mask/preserve unrelated bits.

### Accent — CONFIRMED read mapping
`ACCENT = data[223] & 0x7F`
Controlled values observed directly: 0→`00`, 1→`01`, 2→`02`, 127→`7F`.

## Preset/store SysEx observed in hardware captures

- Name write command observed: `0x23` (example name `Test1`).
- Name read command observed: `0x24`; `Test1` was read back successfully.
- Large preset bulk write command observed in successful sequence: `0x28`, 304-byte SysEx frame.
- Store/ack sequence around `0x11`, `0x23`, `0x28`, `0x33`, Program Change, `0x32`, followed by another `0x37` READ is preserved verbatim in the raw capture appendix.
- Exact semantic meaning of every field inside `0x28` is **NOT CONFIRMED**.

## FX hardware tests — CONFIRMED

- MODULATION TYPE CC95 (`0x5F`): Chorus=`0`, Phaser=`42 (0x2A)`, Flanger=`84 (0x54)`.
- REVERB TYPE CC107 (`0x6B`): Hall=`0`, Plate=`32 (0x20)`, Reverse=`64 (0x40)`, Spring=`96 (0x60)`.
- DELAY TYPE hardware/editor test values: Mono=`0`, Stereo=`25`, Doubler=`50`, Ping Pong=`75`, LCR=`100`.
- Editor-only submodes confirmed separately: Chorus Mode, Phaser Color, Delay Sync.
- FX faders and hardware→GUI response were confirmed working in the v1.45 test branch.

## Flash / sequencer research state

### Preset flash slot — strong structural findings
- Preset slot size: `0x1000` (4096 bytes).
- Strong current map: `0x101..0x380` = 640 bytes = **64 × 10-byte step records**.
- Formula: `step_offset = 0x101 + step_index * 10`, `step_index=0..63`.

### 10-byte step record — current status
```text
+0  step control / flags          HIGH CONFIDENCE structure
+1  Note 1                       HIGH CONFIDENCE
+2  Velocity 1                   HIGH CONFIDENCE
+3  extra 1 / duration candidate HIGH CONFIDENCE candidate
+4  Note 2                       HIGH CONFIDENCE
+5  Velocity 2                   HIGH CONFIDENCE
+6  extra 2 / duration candidate HIGH CONFIDENCE candidate
+7  Note 3                       HIGH CONFIDENCE
+8  Velocity 3                   HIGH CONFIDENCE
+9  extra 3 / duration candidate HIGH CONFIDENCE candidate
```
- `FF` in note slots behaves as an unused/empty note slot.
- Example single-note record: `01 2E 7C 02 FF FF FF FF FF FF`.
- Example 3-note record: `01 39 3A 01 3C 44 01 40 45 01` → notes 57/60/64 with velocities 58/68/69.
- `+3/+6/+9` repeat per voice and show a broad internal range, therefore they are strong duration/length candidates, but **NOT CONFIRMED** as LENGTH.
- `+0` uses values in `0x00..0x3F`, strongly indicating a 6-bit packed control/flag field. Exact Gate/Tie/Accent bit assignment in flash is still **NOT CONFIRMED**.
- Do not copy state-dump offsets 220/221/223 directly onto flash step offsets; these are different structures.

## Firmware/DFU static research preserved

- Updater contains USB DFU/DfuSe payload handling; MIDI/SysEx appears to be used for bootloader entry/handshake.
- Confirmed boot SysEx from updater static analysis: `F0 00 21 1A 02 01 11 00 42 4F 4F 54 20 55 4E 4F 00 F7` (`BOOT UNO\0`).
- **Do not send this command during editor testing** unless bootloader entry is explicitly intended.
- Preset DFU strong map: preset 1 at `0x09F000`; each slot `0x1000`; 128 populated factory slots.

## Source capture inventory

- `uno_capture_20260901_162319.txt` (254 bytes)
- `uno_monitor_capture_20260907_181724.txt` (486 bytes)
- `uno_monitor_capture_20260907_182150.txt` (596 bytes)
- `uno_proxy_capture_20260901_212538.txt` (1243 bytes)
- `uno_proxy_capture_20260901_213043.txt` (1244 bytes)
- `uno_proxy_capture_20260901_213222.txt` (1244 bytes)
- `uno_proxy_capture_20260901_213328.txt` (1244 bytes)
- `uno_proxy_capture_20260901_213527.txt` (1243 bytes)
- `uno_proxy_capture_20260901_213630.txt` (1244 bytes)
- `uno_proxy_capture_20260901_214056.txt` (1243 bytes)
- `uno_proxy_capture_20260901_214155.txt` (1244 bytes)
- `uno_proxy_capture_20260901_214749.txt` (1243 bytes)
- `uno_proxy_capture_20260901_214901.txt` (1243 bytes)
- `uno_proxy_capture_20260901_214957.txt` (1244 bytes)
- `uno_proxy_capture_20260901_215110.txt` (1244 bytes)
- `uno_proxy_capture_20260901_215521.txt` (1244 bytes)
- `uno_proxy_capture_20260901_215632.txt` (1244 bytes)
- `uno_proxy_capture_20260901_215742.txt` (1244 bytes)
- `uno_proxy_capture_20260901_221050.txt` (4522 bytes)
- `uno_proxy_capture_20260901_221904.txt` (1367 bytes)
- `uno_proxy_capture_20260901_224615.txt` (1494 bytes)



# COMPLETE DATA-TRANSFER / PROTOCOL RESEARCH

This section is the consolidated protocol notebook. Confidence labels are mandatory: CONFIRMED = observed/verified; STRONG = structural/static evidence; NOT CONFIRMED = hypothesis only.

## 1. Transport layers
- Standard MIDI over USB/DIN: Note On/Off, CC, Bank Select, Program Change, MIDI Clock/Start/Stop.
- Manufacturer SysEx prefix observed throughout: `F0 00 21 1A ... F7` (IK Multimedia manufacturer ID `00 21 1A`).
- USB DFU/DfuSe is used by the official firmware updater for firmware/preset flash payload transfer. MIDI/SysEx in the updater is used for device communication/bootloader entry, not as evidence that the firmware image itself is streamed as ordinary MIDI SysEx.

## 2. Official MIDI / CC layer
CONFIRMED from official MIDI chart and hardware tests where noted. Important known CCs include: Bank Select CC0; Mod Wheel CC1; Glide 5; VCA 7; Swing 9; OSC waves 12/13/14; OSC tune 15/16/17; OSC levels 18/19/20; Noise 21; OSC sync 22/23; Ring 24; FM 25/26; Filter1 cutoff/res/mode/env/keytrack 28/29/30/31/32; Filter2 cutoff/res 35/36; LFO1 wave/rate/fade/sync 44/45/46/47; LFO2 wave/rate/fade/sync 48/49/50/51; Filter ENV 53-58; Amp ENV 59-63; Matrix amount slots 66-81; Drive 90; Reverb Amount 91; Delay Amount 92; Mod Amount 93; Mod Type 95; Mod Intensity 96; Mod Rate 97; Chorus Mode 98; Delay Type 100; Delay Sync 101; Delay Time L/R 102/103; Delay Feedback 104; Delay Filter 105; Reverb Type 107; Pre-delay 108; reverb time controls 109-112; Size 113; Filter 114.

Hardware-confirmed FX enumerations:
- CC95 MOD TYPE: CHORUS=0, PHASER=42, FLANGER=84.
- CC107 REVERB TYPE: HALL=0, PLATE=32, REVERSE=64, SPRING=96.
- DELAY TYPE raw sequence: MONO=0, STEREO=25, DOUBLER=50, PING PONG=75, LCR=100.
- Editor/hardware tests also confirmed Chorus Mode, Phaser Color and Delay Sync behavior.
- Matrix Amount CC66-81 works. Matrix Source/Destination/Fade In mappings are NOT CONFIRMED; do not invent CCs.

## 3. Bank / Program Change
Official behavior confirms Program Change recalls presets. Current editor research uses Bank Select CC0 + Program Change to address the 256 preset space. Exact bidirectional behavior in the custom editor remains hardware-test dependent; avoid echoing received program changes back to the synth.

## 4. Observed SysEx command family
All observed/researched messages use `F0 00 21 1A ... F7`. The following command bytes/messages have appeared in captures or static research:
- `... 02 03 34 06 01 ...` / `...34 06 00...` observed, followed by `...02 03 00 35 F7`. Semantics not fully confirmed.
- `F0 00 21 1A 02 03 00 3C F7` observed repeatedly. Semantics NOT CONFIRMED.
- `0x23` appears in preset-name write context; observed with ASCII `Test1`.
- `0x24` appears in preset-name read/response context.
- `0x28` appears as a large preset/bulk-write message in a real save/store workflow. It is real protocol evidence, but field-by-field payload semantics are not yet fully decoded.
- `0x37` identifies the current-state response discussed below.
- External/community evidence suggests a `0x36` load-current-patch style SysEx for UNO Synth Pro, but this is NOT promoted to CONFIRMED until verified against our own hardware/captures.

## 5. 309-byte current-state SysEx (`0x37`)
CONFIRMED capture shape:
- total message length: 309 bytes.
- example prefix: `F0 00 21 1A 02 03 00 37 00 00 ... F7`.
- first 10 bytes are treated as protocol/header area in current analysis; `sx[10:-1]` gives 298 encoded payload bytes.
- 298 bytes exactly matches the expansion expected for 260 raw bytes under a 7-bit MIDI packing scheme (`260 + ceil(260/7) = 298`). Several mask-first unpack variants produce 260 bytes. Exact packing convention is still NOT CONFIRMED.
- unpacked state does not directly equal the start of a 4096-byte flash preset slot. Therefore the 309-byte state response is a serialized/projected edit-state structure, not a raw flash-slot copy.

### Confirmed sequencer edit-state fields inside the 309-byte response
- Direction: byte 219 contains a composite field. Direction must be masked, not read as the entire byte. Current evidence: `byte219 & 0x30`; Forward=`0x00`, Backward=`0x10`, Back'n'Forth=`0x20`. A Forward capture had byte219=`0x02`, proving unrelated low bits coexist.
- GATE: offsets 220/221. `gate_raw=(data[221]<<7)|(data[220]&0x60)`; `gate=gate_raw/32`; hardware range 0..10.
- TIE: offset220 mask `0x10`; `tie=bool(data[220]&0x10)`.
- ACCENT: offset223; `accent=data[223]&0x7F`; range 0..127.
- Critical write rule: byte220 is composite. Never overwrite the whole byte when changing Gate/Tie; mask only `0x60` and/or `0x10`, preserving unrelated bits.
- VELOCITY: a separate editable step-velocity field in this 309-byte structure has NOT been confirmed. Incoming MIDI Note On velocity is known and can be captured independently.
- LENGTH: hardware exposes LENGTH range 0.1-64, but exact field in the 309-byte response remains NOT CONFIRMED.

## 6. Official updater static analysis
Updater file studied statically (NOT executed): `UNO Synth Pro Firmware Updater.exe`.
- size 9,385,472 bytes.
- SHA256 `a41399723637cad7195e50362d5afa75751b98e761fc3082e3dfbabc7055776c`.
- PE32+ Windows GUI x86-64, 7 sections.
- strings/resources identify `UNO Synth Pro Firmware Updater`, firmware-version text, MIDI connection, `Entering Bootloader Mode`, DFU progress, `Updating Presets`, `dfu-util`, `dfu-prefix.exe`, `dfu-suffix.exe`, `dfu-util-static.exe`, `dfu-util.exe`, `USP_FW_Main.dfu`, `USP_Presets.dfu`, `DfuSe`.
- WINMM imports include MIDI input/output open/close/start/stop/reset plus `midiOutLongMsg` and `midiOutShortMsg`. Static code path indicates <=3-byte non-F0 messages use short MIDI; SysEx/long data use MIDIHDR + long-message API.

### Bootloader SysEx
CONFIRMED from updater static construction:
`F0 00 21 1A 02 01 11 00 42 4F 4F 54 20 55 4E 4F 00 F7`
ASCII payload: `BOOT UNO\0`.
Fields `02 01 11 00` are not fully semantically decoded. This command is potentially disruptive because it is strongly tied to bootloader entry. DO NOT send during ordinary editor testing.

## 7. Extracted DfuSe payloads
Two embedded DfuSe blobs were extracted during research:
- main firmware blob: 622,925 bytes; DfuSe target `UNO Synth Pro`, alt0; element payload size 622,632 (`0x98028`); SHA256 `c7d25ee09e456795760a2a30f14a48417ca06aa3ded13486a8c12794ca82216c`.
- preset-bank blob: 1,454,373 bytes; alt1; element address `0x0009D000`; element size `0x163000` = 1,454,080; ends exactly at `0x00200000`; SHA256 `4c5db673e675df4e809778588fb59737c0b4ad0da5fda5a2bbee699a58050e2`.

## 8. Preset DFU / flash map
Strong/confirmed structural map from preset-bank DFU:
- `0x09D000`: metadata/service region.
- `0x09E000`: second metadata/service region.
- preset 1 starts `0x09F000`.
- each preset slot = `0x1000` = 4096 bytes.
- formula: `preset_address = 0x09F000 + (preset_number-1)*0x1000`.
- preset 128 begins `0x11E000`.
- `0x11F000-0x19FFFF`: large erased/FF region in studied factory image.
- `0x1A0000`: TEMPLATE/service area.
- `0x1A1000`: factory-name table; duplicate name table around `0x1A2000`.
- name table begins near `0x1A1002`, stride 31 bytes, duplicated +`0x1000`.
- exactly 128 populated factory preset slots were identified in the studied preset DFU. This does not contradict the instrument's 256 user-addressable preset capability; it describes this specific factory DFU image.

## 9. 4096-byte preset slot structure
Current structural map:
- `0x000-0x0FF`: synth/global preset-state candidate, strong inference.
- `0x100`: separate service/header byte; `00` in all 128 studied factory presets.
- `0x101-0x380`: exactly 64 x 10-byte sequencer step records. VERY STRONG structural confirmation.
- `0x381-0x3A1`: 33-byte preset-specific seq/arp metadata block; exact semantics unknown.
- `0x3A2+`: additional structures; an earlier claim that apparent 6-byte patterns were CC automation records was RETRACTED because large blocks repeat identically across unrelated presets.
- later slot space is mostly zero; final bytes may contain trailer/checksum/metadata-like data, not decoded.

## 10. Exact 10-byte flash sequencer-step record
Formula: `step_offset = 0x101 + step_index*10`, `step_index=0..63`. Step64 begins `0x377` and ends at `0x380`. The complete `0x101-0x380` block is 640 bytes and was unique across all 128 studied factory presets, strongly supporting per-preset sequence storage.

Record structure currently established:
```text
+0  step control / 6-bit field (0x00..0x3F)
+1  Note 1
+2  Velocity 1
+3  Note 1 extra  (strong LENGTH/duration candidate, NOT CONFIRMED)
+4  Note 2
+5  Velocity 2
+6  Note 2 extra  (strong LENGTH/duration candidate, NOT CONFIRMED)
+7  Note 3
+8  Velocity 3
+9  Note 3 extra  (strong LENGTH/duration candidate, NOT CONFIRMED)
```
Examples from factory data:
- `01 2E 7C 02 FF FF FF FF FF FF` -> one active note: MIDI 46, velocity 124, extra=2; `FF` marks unused voices.
- `01 39 3A 01 3C 44 01 40 45 01` -> three notes 57/60/64 with velocities 58/68/69 and extra=1 each.
- extra fields can exceed 127 (e.g. `A0`=160), so they are raw flash bytes rather than ordinary 7-bit MIDI values. Their repetition per voice strongly suggests a per-note property. LENGTH/duration is the leading candidate because hardware LENGTH exists, but this remains NOT CONFIRMED.
- `+0` always lies in `0x00..0x3F` in the factory corpus; 63 distinct values observed. Frequent values included `0x3F`, `0x2F`, `0x1F`, `0x0F`, `0x01`, `0x2A`, `0x00`. It is clearly a 6-bit control/value field, but exact Gate/Tie/Accent bit assignment is NOT CONFIRMED.
- Do NOT transfer 309-byte state-dump masks (`220/221/223`) directly to flash step byte `+0`; the state serialization and flash structures are different.

## 11. Candidate envelope blocks in flash
Two adjacent 11-byte blocks were identified at `0x04B-0x055` and `0x056-0x060`. Each resembles five big-endian uint16 values plus one flag byte. Example factory bytes: `0B 32 03 E8 0B B8 0B B8 1F 40 00`, repeated for the second block in one preset. Across factory presets the five 16-bit values vary plausibly. By duplication/location these are HIGH-confidence FILTER ENV / AMP ENV candidates, but exact ADSR field assignments are NOT CONFIRMED.

## 12. `.unosyp` / editor transfer evidence
The official editor supports moving presets between computer library and hardware and can send/receive SysEx in DAW workflows. Our project uses `.unosyp` as the preset extension. Binary format decoding is incomplete; filename management must not be confused with semantic decode. External reverse-engineering evidence shows UNO Synth Pro `.unosyp` payloads and a proposed `0x36` SysEx conversion, but until reproduced on our hardware it remains external evidence only.

## 13. MIDI transport / sequencer playback
MIDI Clock, Start and Stop are separate real-time MIDI transport messages, not SysEx. Current custom-editor sequencer playback work uses clock ticks and software Note On/Off plus validated automation CCs. A 16th-note step corresponds to 6 MIDI clocks under standard 24 PPQN interpretation. Direction Forward/Backward/Back'n'Forth must be handled separately from note data.

## 14. Safety / confidence rules for future protocol work
1. Never label a guessed SysEx field or flash byte CONFIRMED without a controlled differential capture, exact static-code construction, or equivalent direct evidence.
2. Never send the bootloader SysEx during normal editor development.
3. Never overwrite composite bytes wholesale when masks are known (especially state byte220).
4. Keep 309-byte state serialization, `.unosyp` file format, `0x28` bulk payload, and 4096-byte flash slot as separate structures until an exact transform is demonstrated.
5. Retracted hypotheses remain retracted: specifically, `0x3A2+` is NOT currently confirmed as CC automation records.
6. Preserve raw captures verbatim below this research summary.
7. Future confirmed discoveries must be added to this file and to `MIDI_REFERENCE.md` with CONFIRMED / NOT CONFIRMED status.


## RAW CAPTURES — verbatim
The following preserved capture contents are appended verbatim so future analysis does not depend on another chat branch.


### uno_capture_20260901_162319.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.5 Research
Input: 0: UNO Synth Pro
Output: 1: UNO Synth Pro
REC	TIME	TYPE	HEX	DECODED
1	4.544012	SysEx	F0 00 21 1A 02 03 34 06 01 F7	SysEx (10 bytes)
2	4.544596	SysEx	F0 00 21 1A 02 03 00 35 F7	SysEx (9 bytes)
```


### uno_monitor_capture_20260907_181724.txt
```text
UNO Synth Pro MIDI Monitor v1.0 Standalone Safe
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
Clock captured: False
Active Sense captured: False
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	1.208834	UNO→EDITOR	MIDI	3	B0 5F 2A	CC ch 1 5F 2A
2	1.808608	UNO→EDITOR	MIDI	3	B0 5F 54	CC ch 1 5F 54
3	6.628705	UNO→EDITOR	MIDI	3	B0 5F 2A	CC ch 1 5F 2A
4	7.009200	UNO→EDITOR	MIDI	3	B0 5F 00	CC ch 1 5F 00
```


### uno_monitor_capture_20260907_182150.txt
```text
UNO Synth Pro MIDI Monitor v1.0 Standalone Safe
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
Clock captured: False
Active Sense captured: False
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	1.082438	UNO→EDITOR	MIDI	3	B0 6B 20	CC ch 1 6B 20
2	1.867459	UNO→EDITOR	MIDI	3	B0 6B 40	CC ch 1 6B 40
3	2.412684	UNO→EDITOR	MIDI	3	B0 6B 60	CC ch 1 6B 60
4	5.687808	UNO→EDITOR	MIDI	3	B0 6B 40	CC ch 1 6B 40
5	5.903516	UNO→EDITOR	MIDI	3	B0 6B 20	CC ch 1 6B 20
6	6.803660	UNO→EDITOR	MIDI	3	B0 6B 00	CC ch 1 6B 00
```


### uno_proxy_capture_20260901_212538.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	4.810349	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 47 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 40 02 00 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_213043.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	77.903875	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 47 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 50 02 00 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_213222.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	52.946299	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 47 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 50 02 00 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_213328.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	16.524427	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 47 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 40 02 00 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_213527.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	3.484650	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 47 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 50 02 00 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_213630.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	12.987208	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 47 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 40 02 00 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_214056.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	5.646849	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 47 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 00 00 00 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_214155.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	10.809605	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 47 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 20 00 00 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_214749.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	7.370199	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 47 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 40 00 00 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_214901.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	4.350137	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 47 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 60 00 00 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_214957.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	22.677818	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 47 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 40 02 00 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_215110.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	39.159543	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 47 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 00 01 00 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_215521.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	84.226448	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 47 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_215632.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	60.535299	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 47 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 00 01 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_215742.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	61.758667	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 47 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 00 01 00 7F 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_221050.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	38.241410	UNO→EDITOR	MIDI	3	90 31 02	Note On ch 1 31 02
2	38.457007	UNO→EDITOR	MIDI	3	80 31 7F	Note Off ch 1 31 7F
3	77.966523	EDITOR→UNO	SysEx	10	F0 00 21 1A 02 03 37 00 00 F7	SysEx (10 bytes)
4	77.976403	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 01 00 04 00 40 27 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 00 01 00 7F 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
5	77.986583	EDITOR→UNO	SysEx	10	F0 00 21 1A 02 03 11 01 0A F7	SysEx (10 bytes)
6	77.989284	UNO→EDITOR	SysEx	9	F0 00 21 1A 02 03 00 11 F7	SysEx (9 bytes)
7	78.006684	EDITOR→UNO	SysEx	16	F0 00 21 1A 02 03 23 01 01 3A 54 65 73 74 31 F7	SysEx (16 bytes)
8	78.300253	UNO→EDITOR	SysEx	9	F0 00 21 1A 02 03 00 23 F7	SysEx (9 bytes)
9	78.306670	EDITOR→UNO	SysEx	304	F0 00 21 1A 02 03 28 01 3A 60 00 04 00 40 27 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 00 01 00 7F 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	SysEx (304 bytes)
10	78.550280	UNO→EDITOR	SysEx	12	F0 00 21 1A 02 03 00 28 01 3A 01 F7	SysEx (12 bytes)
11	78.556595	EDITOR→UNO	SysEx	10	F0 00 21 1A 02 03 33 01 3B F7	SysEx (10 bytes)
12	78.564231	UNO→EDITOR	SysEx	9	F0 00 21 1A 02 03 00 33 F7	SysEx (9 bytes)
13	78.615227	UNO→EDITOR	MIDI	2	C0 3A	Program ch 1 3A
14	78.615746	UNO→EDITOR	SysEx	12	F0 00 21 1A 02 03 32 01 3B 01 3B F7	SysEx (12 bytes)
15	78.616556	EDITOR→UNO	SysEx	10	F0 00 21 1A 02 03 37 00 00 F7	SysEx (10 bytes)
16	78.648431	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 00 00 04 00 40 27 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 00 01 00 7F 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
17	79.143713	EDITOR→UNO	SysEx	11	F0 00 21 1A 02 03 24 01 01 3A F7	SysEx (11 bytes)
18	79.192395	UNO→EDITOR	SysEx	43	F0 00 21 1A 02 03 00 24 01 01 3A 54 65 73 74 31 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 F7	SysEx (43 bytes)
```


### uno_proxy_capture_20260901_221904.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	14.685298	UNO→EDITOR	MIDI	3	90 30 01	Note On ch 1 30 01
2	14.878166	UNO→EDITOR	MIDI	3	80 30 7F	Note Off ch 1 30 7F
3	50.331581	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 01 3A 01 3A 00 00 04 00 40 27 00 00 00 01 00 00 08 40 12 00 00 64 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 7C 0F 30 27 18 00 00 00 00 00 00 00 00 00 00 00 08 00 0A 00 00 00 00 00 7C 03 40 01 00 00 64 02 00 00 00 00 00 00 64 02 00 00 00 00 00 00 00 00 00 60 70 47 00 4F 0B 26 2C 18 61 03 05 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 00 0C 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 73 71 03 50 00 08 10 00 20 06 00 1E 0F 1E 28 04 38 30 00 00 32 00 70 79 78 01 08 00 00 01 48 75 20 26 40 66 00 17 48 01 60 03 00 0F 00 01 20 01 00 10 20 41 04 04 7E 7F 7F 20 00 01 00 7F 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Back'n'Forth | byte[219]=0x20
```


### uno_proxy_capture_20260901_224615.txt
```text
UNO Synth Pro MIDI / SysEx Monitor v0.8 Proxy Research
UNO IN: 0: UNO Synth Pro
UNO OUT: 1: UNO Synth Pro
EDITOR OUT/TAP IN: 1: UNO_TAP
EDITOR IN/RETURN OUT: 3: UNO_RETURN
REC	TIME	DIRECTION	TYPE	BYTES	HEX	DECODED
1	10.453172	UNO→EDITOR	MIDI	2	C0 3A	Program ch 1 3A
2	10.453519	UNO→EDITOR	SysEx	12	F0 00 21 1A 02 03 32 00 3B 00 3B F7	SysEx (12 bytes)
3	13.765286	EDITOR→UNO	SysEx	10	F0 00 21 1A 02 03 37 00 00 F7	SysEx (10 bytes)
4	13.776759	UNO→EDITOR	SysEx	309	F0 00 21 1A 02 03 00 37 00 00 00 3A 00 3A 00 00 04 00 60 18 60 42 7F 01 00 00 00 40 13 01 58 64 00 18 15 40 17 19 00 00 00 00 18 06 00 00 00 00 00 64 04 70 73 1F 32 02 00 00 60 00 40 0A 00 24 00 00 20 08 0F 45 03 00 00 7C 03 00 00 01 00 1A 06 00 00 30 00 00 00 64 02 00 00 00 00 00 00 14 00 00 40 10 03 00 64 00 10 03 40 7C 03 10 00 0B 64 0C 40 3E 01 6E 05 38 3F 00 02 30 41 0C 0F 1F 00 01 58 20 46 42 0F 40 1C 09 08 70 00 00 32 1E 3E 00 0A 70 60 00 00 64 00 60 73 71 03 50 00 07 00 10 53 30 00 7A 00 03 06 00 20 06 00 1E 05 01 64 05 38 30 00 00 32 00 70 79 78 01 08 00 01 03 48 75 20 26 60 6D 00 2D 48 01 28 02 60 12 2B 01 64 00 00 10 40 02 03 02 6C 25 7F 02 50 02 00 00 00 00 58 01 40 43 00 29 00 7C 10 00 04 00 05 11 3A 00 10 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 F7	UNO state 309B | Seq Direction=Forward | Gate=10 | Tie=ON | Accent=0 | byte[219]=0x02
```
