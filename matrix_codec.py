"""Canonical UNO Synth Pro modulation-matrix FILE codec.

Namespaces are kept strictly separate and all of them come from one table,
``UNO_MATRIX_FULL_REGISTRY.csv``:

- ``file_raw_dec``   the identifier actually stored in the native preset
- ``wire_raw_dec``   the identifier used by live SysEx (0x3E), never persisted
- ``ui_position_0based``  order of the entry in the editor selector

A UI index is therefore never used as a FILE identifier.  The registry is
validated on import: a file id that is missing, duplicated, or out of order
raises instead of silently shifting every destination above it.

Geometry (validated by the controlled matrix corpus, see
Docs/history/STEP_AUTOMATION_CANONICAL_DECODER_2026-09-23.md):
each route owns a 32-bit cell at ``MATRIX_BIT + slot*32``; the 6-bit source id
straddles the leading boundary -- low 3 bits at ``base-3``, high 3 bits at
``base+0``.
"""
from dataclasses import dataclass
from pathlib import Path

REGISTRY_CSV = Path(__file__).with_name('UNO_MATRIX_FULL_REGISTRY.csv')

FILE_STATE_SIZE = 297
RAW_STATE_SIZE = 260
MATRIX_BIT = 188 * 8
ROUTE_BITS = 32
ROUTE_COUNT = 16
AMOUNT_MIN = -63
AMOUNT_MAX = 64
FADE_MAX = 255


@dataclass(frozen=True)
class MatrixParameter:
    key: str
    name: str
    ui_index: int
    file_id: int
    wire_id: int


def _load_registry(path=REGISTRY_CSV):
    import csv

    sources, destinations = [], []
    with Path(path).open('r', encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            kind = row['kind'].strip().lower()
            selectable = row['selectable_in_ui'].strip() == '1'
            ui_text = row['ui_position_0based'].strip()
            item = MatrixParameter(
                f"{kind}_{int(row['file_raw_dec']):02d}",
                row['semantic'].strip(),
                int(ui_text) if ui_text else -1,
                int(row['file_raw_dec']),
                int(row['wire_raw_dec']),
            )
            if kind == 'source':
                sources.append(item)
            elif kind == 'destination':
                destinations.append(item)
            else:
                raise ValueError(f"unknown Matrix registry kind: {kind!r}")

    def validate(kind, rows):
        ids = [x.file_id for x in rows]
        if ids != list(range(len(ids))):
            raise ValueError(f'{kind} FILE ids are incomplete or out of order')
        visible = sorted(x.ui_index for x in rows if x.ui_index >= 0)
        if visible != list(range(len(visible))):
            raise ValueError(f'{kind} UI positions are incomplete')
        if any(x.ui_index == -1 and x in visible for x in rows):
            raise ValueError(f'{kind} hidden rows must not carry a UI position')
        if len({x.wire_id for x in rows}) != len(rows):
            raise ValueError(f'{kind} WIRE ids are not unique')
        if len({x.name for x in rows}) != len(rows):
            raise ValueError(f'{kind} semantic names are not unique')

    validate('source', sources)
    validate('destination', destinations)
    return tuple(sources), tuple(destinations)


SOURCES, DESTINATIONS = _load_registry()
DESTINATION_ALL = DESTINATIONS
DESTINATION_HIDDEN = tuple(x for x in DESTINATIONS if x.ui_index < 0)
DESTINATIONS_VISIBLE = tuple(x for x in DESTINATIONS if x.ui_index >= 0)

SOURCE_BY_FILE = {x.file_id: x for x in SOURCES}
DEST_BY_FILE = {x.file_id: x for x in DESTINATIONS}
SOURCE_BY_NAME = {x.name: x for x in SOURCES}
DEST_BY_NAME = {x.name: x for x in DESTINATIONS}

# Editor selector order.  Index into this list is a UI position only.
MATRIX_DESTINATION_FILE_NAMES = tuple(x.name for x in DESTINATIONS_VISIBLE)
MATRIX_SOURCE_FILE_NAMES = tuple(x.name for x in SOURCES)


def _get_bits(raw, start, width):
    return sum(((raw[(start + i) // 8] >> ((start + i) % 8)) & 1) << i for i in range(width))


def _set_bits(raw, start, width, value):
    if value < 0 or value >= (1 << width):
        raise ValueError(f'value {value} does not fit in {width} bits at {start}')
    for i in range(width):
        pos = start + i
        mask = 1 << (pos % 8)
        if (value >> i) & 1:
            raw[pos // 8] |= mask
        else:
            raw[pos // 8] &= ~mask


def decode_amount(raw):
    raw = int(raw) & 0xFF
    if raw <= 0x40:
        return raw
    if raw >= 0xC1:
        return raw - 256
    return None


def encode_amount(value):
    value = int(value)
    if not AMOUNT_MIN <= value <= AMOUNT_MAX:
        raise ValueError(f'Matrix Amount must be {AMOUNT_MIN}..{AMOUNT_MAX}')
    return value & 0xFF


def decode_matrix(raw):
    """Decode 16 routes from a 260-byte raw (unpacked) state."""
    raw = bytes(raw)
    if len(raw) < RAW_STATE_SIZE:
        raise ValueError('raw state is too short for the modulation matrix')
    routes = []
    for slot in range(ROUTE_COUNT):
        base = MATRIX_BIT + slot * ROUTE_BITS
        source = _get_bits(raw, base - 3, 3) | (_get_bits(raw, base, 3) << 3)
        destination = _get_bits(raw, base + 5, 6)
        amount_raw = _get_bits(raw, base + 21, 8)
        fade_raw = _get_bits(raw, base + 11, 10)
        routes.append({
            'slot': slot,
            'source_file_id': source,
            'source': SOURCE_BY_FILE[source].name if source in SOURCE_BY_FILE else f'FILE 0x{source:02X}',
            'reserved_raw': _get_bits(raw, base + 3, 2),
            'destination_file_id': destination,
            'destination': decode_destination_file_id(destination),
            'fade_raw': fade_raw,
            'fade': (fade_raw // 4) if (fade_raw % 4 == 0 and fade_raw <= FADE_MAX * 4) else None,
            'amount_raw': amount_raw,
            'amount': decode_amount(amount_raw),
        })
    return routes


def encode_matrix(raw, changes):
    """Return raw state bytes with only the named fields of the named slots changed."""
    out = bytearray(raw)
    for slot, change in changes.items():
        slot = int(slot)
        if not 0 <= slot < ROUTE_COUNT:
            raise ValueError('Matrix slot must be 0..15')
        base = MATRIX_BIT + slot * ROUTE_BITS
        if 'source_file_id' in change:
            value = int(change['source_file_id'])
            if not 0 <= value <= 0x3F:
                raise ValueError(f'source FILE id {value} out of range')
            _set_bits(out, base - 3, 3, value & 7)
            _set_bits(out, base, 3, (value >> 3) & 7)
        if 'destination_file_id' in change:
            value = int(change['destination_file_id'])
            if not 0 <= value <= 0x3F:
                raise ValueError(f'destination FILE id {value} out of range')
            _set_bits(out, base + 5, 6, value)
        if 'fade_raw' in change:
            _set_bits(out, base + 11, 10, int(change['fade_raw']))
        elif 'fade' in change:
            fade = int(change['fade'])
            if not 0 <= fade <= FADE_MAX:
                raise ValueError(f'Matrix Fade must be 0..{FADE_MAX}')
            _set_bits(out, base + 11, 10, fade * 4)
        if 'amount_raw' in change:
            _set_bits(out, base + 21, 8, int(change['amount_raw']))
        elif 'amount' in change:
            _set_bits(out, base + 21, 8, encode_amount(change['amount']))
    return bytes(out)


def ui_route_to_file_change(source, destination, amount, fade, source_names=None, destination_names=None):
    """Translate one editor route into FILE fields.

    Accepts a registry name, a raw FILE id, or the ``FILE 0x..`` form produced
    for identifiers that the selector does not expose.  UI positions are never
    accepted as FILE ids.
    """
    change = {}

    def resolve(value, by_name, prefix):
        if isinstance(value, MatrixParameter):
            return value.file_id
        if isinstance(value, int):
            if not 0 <= value <= 0x3F:
                raise ValueError(f'FILE id {value} out of range')
            return value
        if isinstance(value, str) and value.startswith(prefix):
            return int(value[len(prefix):], 16) & 0x3F
        found = by_name.get(value)
        if found is None:
            raise ValueError(f'unknown Matrix entry: {value!r}')
        return found.file_id

    if source is not None:
        change['source_file_id'] = resolve(source, SOURCE_BY_NAME, 'FILE 0x')
    if destination is not None:
        change['destination_file_id'] = resolve(destination, DEST_BY_NAME, 'FILE 0x')
    if amount is not None:
        change['amount'] = int(amount)
    if fade is not None:
        fade = int(fade)
        if not 0 <= fade <= FADE_MAX:
            raise ValueError(f'Matrix Fade must be 0..{FADE_MAX}')
        change['fade'] = fade
    return change


def decode_destination_file_id(file_id):
    file_id = int(file_id) & 0x3F
    item = DEST_BY_FILE.get(file_id)
    return item.name if item is not None else f'FILE 0x{file_id:02X}'


def encode_destination_file_id(value):
    if isinstance(value, MatrixParameter):
        return value.file_id
    if isinstance(value, int):
        if 0 <= value <= 0x3F:
            return value
        raise ValueError(f'FILE id {value} out of range')
    found = DEST_BY_NAME.get(value)
    if found is not None:
        return found.file_id
    if isinstance(value, str) and value.startswith('FILE 0x'):
        return int(value[7:], 16) & 0x3F
    raise ValueError(f'unknown Matrix destination: {value!r}')


def amount_to_wire(value):
    return encode_amount(value) & 0x7F


def amount_to_cc(value):
    return int(value) + 63


def live_destination(slot, destination):
    item = destination if isinstance(destination, MatrixParameter) else DEST_BY_NAME.get(destination)
    wire = item.wire_id if item is not None else int(destination)
    return bytes((0xF0, 0x00, 0x21, 0x1A, 0x02, 0x03, 0x3E, 0x02,
                  int(slot) & 0x0F, 0x01, wire & 0x7F, 0xF7))


def live_amount(slot, amount):
    return bytes((0xF0, 0x00, 0x21, 0x1A, 0x02, 0x03, 0x3E, 0x02,
                  int(slot) & 0x0F, 0x02, amount_to_wire(amount), 0xF7))


def live_fade(slot, fade):
    return bytes((0xF0, 0x00, 0x21, 0x1A, 0x02, 0x03, 0x3E, 0x02,
                  int(slot) & 0x0F, 0x03, int(fade) & 0x7F, 0xF7))
