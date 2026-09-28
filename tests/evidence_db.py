"""Access to the unified evidence database.

The SQLite file under ``tests/fixtures`` is the authoritative record of what
was observed on the device and what remains unresolved.  It is opened
read-only: a test run must never be able to alter the evidence.

Expected failures are declared here as data rather than as silently skipped
assertions, so that a newly mis-saved capture shows up as a change in this
table instead of disappearing into a skip.
"""
from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent / 'fixtures' / 'UNO_UNIFIED_NORMALIZED_FINAL_2026-09-29.sqlite'

# Controlled matrix captures that the database itself does not mark as validated.
# Matrix.zip is recorded in evidence_exclusions 5/6 as containing mis-saved files;
# the user replaced AmpEnvSus and GATE 2 IN. These two were never replaced and
# carry no replacement status, so their source field decodes as 0 ("no source").
UNRESOLVED_MATRIX_CAPTURES = {
    'FiltEnvSus': 'Filter Env Sustain',
    'AmpEnvRel': 'Amp Env Release',
}


def connect():
    if not DB_PATH.exists():
        raise FileNotFoundError(f'evidence database is missing: {DB_PATH}')
    con = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    return con


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
