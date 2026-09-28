"""Access to the unified evidence database.

The canonical database lives in the evidence environment, not in this
repository:

    E:\\UNO_Evidence\\databases\\UNO_UNIFIED_NORMALIZED_FINAL_2026-09-29.sqlite

Set ``UNO_EVIDENCE_DB`` to point somewhere else.  A copy under
``tests/fixtures`` keeps the suite runnable on its own, but it is a snapshot:
when the two disagree, the environment is right.

The database is always opened read-only: a test run must never be able to alter
the evidence.

Expected failures are declared here as data rather than as silently skipped
assertions, so that a newly mis-saved capture shows up as a change in this
table instead of disappearing into a skip.
"""
import os
from pathlib import Path
import sqlite3

ENV_DB = Path(r'E:\UNO_Evidence\databases\UNO_UNIFIED_NORMALIZED_FINAL_2026-09-29.sqlite')
FIXTURE_DB = Path(__file__).resolve().parent / 'fixtures' / 'UNO_UNIFIED_NORMALIZED_FINAL_2026-09-29.sqlite'


def database_path():
    override = os.environ.get('UNO_EVIDENCE_DB')
    if override:
        return Path(override)
    if ENV_DB.exists():
        return ENV_DB
    return FIXTURE_DB


def connect():
    path = database_path()
    if not path.exists():
        raise FileNotFoundError(
            f'evidence database is missing: {path}\n'
            f'expected the environment at {ENV_DB}, or set UNO_EVIDENCE_DB')
    con = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    return con


# Controlled matrix captures that the database itself does not mark as validated.
# Matrix.zip is recorded in evidence_exclusions 5/6 as containing mis-saved files;
# the user replaced AmpEnvSus and GATE 2 IN. These two were never replaced and
# carry no replacement status, so their source field decodes as 0 ("no source").
UNRESOLVED_MATRIX_CAPTURES = {
    'FiltEnvSus': 'Filter Env Sustain',
    'AmpEnvRel': 'Amp Env Release',
}


def matrix_presets(con):
    """Return {pair_key: (bytes, is_replacement)} for every controlled matrix capture."""
    replacements = {r['pair_key']: bytes(r['raw_bytes'])
                    for r in con.execute('SELECT * FROM matrix_controlled_presets')}
    result = {}
    for row in con.execute('SELECT * FROM matrix_hax_files ORDER BY hax_id'):
        key = row['pair_key']
        if key in replacements or key in result:
            continue
        result[key] = (bytes(row['decoded_bytes']), False)
    for key, blob in replacements.items():
        result[key] = (blob, True)
    return result


def corpus_size(con):
    return con.execute('SELECT COUNT(*) FROM unosyp_complete_hex').fetchone()[0]
