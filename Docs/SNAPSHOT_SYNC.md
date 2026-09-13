# Baseline provenance

The earlier sync snapshot preserved legacy FIX2 sources. This ZIP adds the post-FIX2 changes documented in RELEASE_NOTES_v0.9.0-beta.md; it is no longer a byte-for-byte FIX2 snapshot. The reference snapshot and archived v1.29 were not edited. GitHub publication is not part of this build.

# v0.9.0-beta source snapshot

The source baseline is `UNO_Pro_Advanced_v1.64_FIX2.zip` (legacy v1.64 FIX2).
All included source files, Assets and historical Docs are preserved byte for byte.
The adjacent local folder named `UNO_Pro_Advanced_v1.64` is older than FIX2 and
was not used to overwrite the FIX2 snapshot.

Repository version: **v0.9.0-beta**. See `VERSIONING.md`.
Legacy version strings in application source and historical notes are retained.

Excluded captures: `Docs/test2.unosyp`, `Docs/test3.unosyp`,
`Docs/test4.unosyp`, `Docs/test5.unosyp`. Tests that depend on these captures
require private local copies at their original paths. Historical test scripts
are retained as references and may assert behavior from earlier versions.
No temporary files, Python caches or incidental screenshots are included.
The three images in Assets are application resources and are included.

Existing README files, VERSION, versioning/beta documentation and
`Reference/REUSABLE_MUSICAL_RANDOMIZER_ALGORITHMS.md` are retained as repository
supplements. The incomplete snapshot chunks, temporary sync note and one-off
snapshot workflow are removed.
