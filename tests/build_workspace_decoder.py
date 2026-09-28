"""Build the approved canonical Step Automation workspace snapshot."""
from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
BUILD_NAME = "UNO_Pro_Advanced_v0.9.7-beta2-HARDWARE-AUTOMATION-FIX"
SOURCE_ID = "workspace-snapshot-2026-09-23"


def main() -> None:
    if (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip() != BUILD_NAME.removeprefix("UNO_Pro_Advanced_v"):
        raise RuntimeError("VERSION does not match the approved build name")

    release = ROOT / "builds" / BUILD_NAME
    archive = ROOT / "builds" / f"{BUILD_NAME}.zip"
    if release.exists() or archive.exists():
        raise RuntimeError("Historical build already exists; refusing overwrite")

    files = list(ROOT.glob("*.py"))
    files += [ROOT / name for name in (
        "VERSION", "AGENTS.md", "README.md", "README.ru.md", "CHANGELOG.md",
        "PROJECT_INDEX.md", "run_editor.bat", "install_dependencies.bat",
        "state_decoder_map.json",
    )]
    files += list((ROOT / "live_creator").rglob("*.py"))
    files += [path for path in (ROOT / "Docs").rglob("*") if path.is_file()]
    files += [path for path in (ROOT / "Assets").rglob("*") if path.is_file()]
    files += list((ROOT / "tests").glob("*.py"))

    selected = sorted({path for path in files if path.is_file()})
    forbidden = {".unosyp", ".pyc", ".log", ".zip"}
    if any(path.suffix.lower() in forbidden or "__pycache__" in path.parts for path in selected):
        raise RuntimeError("Forbidden file selected for build")
    for path in selected:
        if path.suffix == ".py":
            compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")

    release.mkdir(parents=True)
    manifest: dict[str, str] = {}
    for path in selected:
        relative = path.relative_to(ROOT)
        data = path.read_bytes()
        target = release / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        manifest[relative.as_posix()] = hashlib.sha256(data).hexdigest()

    (release / "BUILD_COMMIT").write_text(SOURCE_ID + "\n", encoding="utf-8")
    (release / "BUILD_DATE").write_text(
        datetime.datetime.now(datetime.timezone.utc).isoformat() + "\n", encoding="utf-8"
    )
    (release / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted(release.rglob("*")):
            if path.is_file():
                zipped.write(path, path.relative_to(release.parent))

    with zipfile.ZipFile(archive) as zipped:
        if zipped.testzip() is not None:
            raise RuntimeError("ZIP CRC check failed")
        for relative, digest in manifest.items():
            packaged = zipped.read(f"{BUILD_NAME}/{relative}")
            if hashlib.sha256(packaged).hexdigest() != digest:
                raise RuntimeError(f"Manifest mismatch: {relative}")
        if any(
            "__pycache__" in name
            or Path(name).suffix.lower() in forbidden
            for name in zipped.namelist()
        ):
            raise RuntimeError("Forbidden content in archive")

    print(f"BUILD / CRC / SHA-256 MANIFEST PASS: {archive}")
    print(f"SOURCE: {SOURCE_ID}")


if __name__ == "__main__":
    main()
