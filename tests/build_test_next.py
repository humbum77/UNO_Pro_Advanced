"""Committed source build for the test/v0.9.7-next branch."""

from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
BUILD_NAME = 'UNO_Pro_Advanced_v0.9.7-next'
REQUIRED_BRANCH = 'test/v0.9.7-next'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def main():
    branch = git('branch', '--show-current')
    if branch != REQUIRED_BRANCH:
        raise RuntimeError(f'Test build requires {REQUIRED_BRANCH}, got {branch or "detached HEAD"}')
    if git('status', '--porcelain'):
        raise RuntimeError('Commit all test-build changes before build')

    release = ROOT / 'builds' / BUILD_NAME
    archive = ROOT / 'builds' / f'{BUILD_NAME}.zip'
    if release.exists() or archive.exists():
        raise RuntimeError('Test build already exists; never overwrite build artifacts')

    files = list(ROOT.glob('*.py'))
    files += [ROOT / name for name in (
        'VERSION', 'AGENTS.md', 'README.md', 'README.ru.md', 'CHANGELOG.md',
        'PROJECT_INDEX.md', 'run_editor.bat', 'install_dependencies.bat',
        'state_decoder_map.json', 'Docs/requirements.txt',
        'Docs/INTEGRATION_v0.9.6-beta.md',
    )]
    files += list((ROOT / 'live_creator').rglob('*.py'))
    files += [ROOT / 'Docs' / name for name in (
        'PROJECT_STATE.md', 'DECISIONS.md', 'RELEASE_PREPARATION.md',
        'RELEASE_NOTES_v0.9.7-beta.md',
    )]
    files += [path for path in (ROOT / 'Assets').rglob('*') if path.is_file()]
    files += list((ROOT / 'tests').glob('*.py'))

    for path in files:
        if path.suffix == '.py':
            compile(path.read_text(encoding='utf-8-sig'), str(path), 'exec')

    release.mkdir(parents=True)
    manifest = {}
    for path in sorted(set(files)):
        relative = path.relative_to(ROOT)
        data = path.read_bytes()
        target = release / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        manifest[relative.as_posix()] = hashlib.sha256(data).hexdigest()

    commit = git('rev-parse', 'HEAD')
    (release / 'BUILD_COMMIT').write_text(commit + '\n', encoding='utf-8')
    (release / 'BUILD_DATE').write_text(
        datetime.datetime.now(datetime.timezone.utc).isoformat() + '\n', encoding='utf-8'
    )
    (release / 'BUILD_CHANNEL').write_text(REQUIRED_BRANCH + '\n', encoding='utf-8')
    (release / 'MANIFEST.json').write_text(
        json.dumps(manifest, indent=2), encoding='utf-8'
    )

    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted(release.rglob('*')):
            if path.is_file():
                zipped.write(path, path.relative_to(release.parent))

    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        for path, digest in manifest.items():
            packaged = zipped.read(f'{BUILD_NAME}/{path}')
            assert hashlib.sha256(packaged).hexdigest() == digest
        assert not any(
            '__pycache__' in name or name.endswith(('.pyc', '.unosyp', '.log'))
            for name in zipped.namelist()
        )

    print('TEST BUILD / CRC / MANIFEST PASS:', archive)
    print('SOURCE COMMIT:', commit)


if __name__ == '__main__':
    main()
