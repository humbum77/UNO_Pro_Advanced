# Changelog

## Native Step Automation writer — 2026-09-24

- `SAVE` / `SAVE AS` now retain binary `.unosyp` when the source preset is
  native; the file is no longer converted to editor JSON.
- Added end-to-end value writing for already-resolved Step Automation targets
  with confirmed value codecs, including multi-step cumulative pages.
- Native preset state, page cores, target Selection/Alignment and unresolved
  automation bytes are preserved exactly.
- Target-set additions/removals and unconfirmed WAVE/CUTOFF boundary encodings
  fail explicitly instead of producing a corrupt preset.

## Step Automation codec follow-up — 2026-09-24

- Recognized equivalent DRIVE/DELAY order variants `C0/C8`.
- Added inverse `pack7` and a byte-exact native extension writer primitive.
- Validated binary round-trip on 450 `.unosyp` files without mismatches.
- Arbitrary target generation and hardware STORE remain explicitly partial.

## 0.9.7-beta2 hardware automation fix — 2026-09-23

- Added one restricted read-only Step Automation decoder shared by factory
  `.unosyp` files and hardware SysEx `0x29` pages.
- Fixed the hardware adapter so decoded automation reaches
  `Sequence.automation`.
- Added the factory `[053] FAKE 808` regression: `CUTOFF 1` on steps
  6, 7, 11, 23, 27, 54, 55 and 59.
- Enforced the hardware limit of 18 automation entries per step.
- Unknown or ambiguous combinations remain raw; no universal selection
  decoder or writer is claimed.
- The earlier `CANONICAL-STEP-DECODER` artifact is invalid. Use
  `UNO_Pro_Advanced_v0.9.7-beta2-HARDWARE-AUTOMATION-FIX.zip`.

## 0.9.7-beta — 2026-09-17

- Объединён декодер секвенсора локальных `.unosyp` и аппаратных страниц SysEx `0x29`.
- Добавлено подтверждённое декодирование Gate, Accent и TIE в обеих ветвях загрузки.
- Аппаратный приём расширен до страниц 0–4 для полного чтения секвенсора.
- Применён патч анимации огибающей.
- Визуальный отрезок S–R огибающей увеличен на 30%.
- Новая огибающая и код её анимации зафиксированы как `LOCKED / НЕ ИЗМЕНЯТЬ` без прямого указания пользователя.
- Версия интерфейса и `VERSION` обновлены до 0.9.7-beta.

## 0.9.6-beta

- Интегрирован Live Creator в основную beta-линию UNO Pro Advanced.
