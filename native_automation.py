"""Step Automation decoding, lane integration and guarded native value writing."""

PARAMETER_TO_LANE = {
    'WAVE1': 'WAVE 1', 'TUNE1': 'TUNE 1', 'WAVE2': 'WAVE 2',
    'TUNE2': 'TUNE 2', 'WAVE3': 'WAVE 3', 'TUNE3': 'TUNE 3',
    'LEVEL1': 'LEVEL 1', 'LEVEL2': 'LEVEL 2', 'LEVEL3': 'LEVEL 3',
    'CUTOFF1': 'CUTOFF 1', 'RES1': 'RESONANCE 1', 'ENV1': 'ENV AM 1',
    'CUTOFF2': 'CUTOFF 2', 'RES2': 'RESONANCE 2', 'ENV2': 'ENV AM 2',
    'SPACING': 'SPACING', 'LFO1': 'LFO 1', 'LFO2': 'LFO 2',
    'DRIVE': 'DRIVE AMOUNT', 'MOD': 'MODULATION AMOUNT',
    'DELAY': 'DELAY AMOUNT', 'REVERB': 'REVERB AMOUNT',
}


def normalize_decoded(native):
    """Convert the canonical decoder result into the editor's native envelope."""
    parameters = native.get('parameters', [])
    entries = [
        {'raw_hex': item['native_hex'], 'parameter': item['name'],
         'value': item.get('value', item['native_signed']
                           if item.get('native_signed') is not None
                           else item.get('native_unsigned')),
         'step': item.get('step', native.get('step')),
         'record_index': item.get('record_index', 0),
         'payload_offset': item.get('payload_offset', 0)}
        for item in parameters
    ]
    return {'status': 'CAPTURE_PROFILE' if native.get('profile') else 'PARTIAL',
            'step': native.get('step'), 'entry_count': native.get('count', 0),
            'selection_hex': native.get('selection_hex', ''),
            'payload_hex': native.get('values_hex', ''),
            'pages_match': native.get('pages_match', False),
            'profile': native.get('profile'), 'entries': entries,
            'mapping': native.get('status', ''),
            'records': native.get('records', []), 'maximum_entries': 18}


def apply_decoded_to_sequence(sequence, native):
    """Expose every resolved native point through the matching editor lane."""
    normalized = normalize_decoded(native)
    decoded_points = 0
    for entry in normalized['entries']:
        parameter = PARAMETER_TO_LANE.get(entry.get('parameter'))
        step = int(entry.get('step') or 0) - 1
        if parameter is None or not 0 <= step < 64:
            continue
        lane = next((item for item in sequence.automation
                     if item.get('parameter') == parameter), None)
        value = entry.get('value')
        if lane is None or value is None:
            continue
        values = lane.setdefault('values', [None] * 64)
        while len(values) < 64:
            values.append(None)
        values[step] = value
        decoded_points += 1
    normalized['decoded_lane_points'] = decoded_points
    if normalized.get('profile') and normalized['entries'] and not decoded_points:
        raise ValueError('Recognized native automation was not mapped to an editor lane')
    sequence.native_automation = normalized
    return normalized


def read_automation(data):
    # Variable-length pages have 32-bit length headers. Legacy 1081-byte files
    # use a different layout; preserve the existing opaque reader for them.
    if len(data)>1081:
        from uno_step_automation_decoder import decode
        native=decode(bytes(data))
        return normalize_decoded(native)
    if len(data)<496:raise ValueError('Truncated automation header')
    size=data[494]
    if size%2:raise ValueError('Unsupported odd automation payload length')
    if 496+size>len(data):raise ValueError('Truncated automation payload')
    payload=data[496:496+size]
    return {'status':'PARTIAL','payload_length':size,'entry_count':size//2,
            'unknown_byte_495':data[495], 'payload_hex':payload.hex(),
            'entries':[{'raw_hex':payload[i:i+2].hex(),'parameter':None,'value':None,'step':None} for i in range(0,size,2)],
            'mapping':'UNKNOWN', 'maximum_entries':None}

def sequence_length(data):
    if len(data)<209 or data[207]>127 or data[208]>127:raise ValueError('Invalid length field')
    value=data[207] | (data[208]<<7)
    length=(value+1)//8
    if not 1<=length<=64 or value!=length*8-1:raise ValueError('Unsupported length encoding')
    return length

def encode_sequence_length(data,length):
    if type(length)is not int or not 1<=length<=64:raise ValueError('Length must be 1..64')
    if len(data)<209:raise ValueError('Truncated length field')
    result=bytearray(data);value=length*8-1
    result[207]=value&127;result[208]=value>>7
    return bytes(result)



def encode_sequence_gate_accent(data, gate_value, accent_value):
    """Write confirmed shared sequencer Gate/Accent values to native preset state."""
    if len(data) < 213:
        raise ValueError('Truncated Gate/Accent state')
    gate=max(0,min(10,int(gate_value)));accent=max(0,min(127,int(accent_value)))
    gate_raw=16 if gate==0 else gate*32+16
    result=bytearray(data);result[209]=gate_raw&127;result[210]=(gate_raw>>7)&127;result[212]=accent
    return bytes(result)

def _same_route(before, change):
    if not isinstance(before, dict):
        return False
    if 'source_file_id' in change and int(before.get('source', -1)) != change['source_file_id']:
        return False
    if 'destination_file_id' in change and int(before.get('destination', -1)) != change['destination_file_id']:
        return False
    if 'amount' in change and before.get('amount') != change['amount']:
        return False
    if 'fade' in change and before.get('fade') != change['fade']:
        return False
    return True


def matrix_routes_to_changes(matrix, original=None):
    """Translate the editor's per-route state into native FILE changes.

    Each entry is ``{source, destination, amount, fade}`` where source and
    destination are native FILE ids.  ``None`` and empty entries mean the route
    is unused and are left untouched rather than cleared: the codec only changes
    fields it is explicitly given.

    When ``original`` (the same shape, as decoded from the file being written) is
    supplied, only routes that actually differ are returned.  That is what keeps
    the three sequencer-overlapping routes out of the write: they are unchanged
    whenever the user did not touch them.
    """
    changes = {}
    for slot, route in enumerate(matrix or []):
        if not isinstance(route, dict):
            continue
        change = {}
        source = route.get('source_file_id', route.get('source'))
        destination = route.get('destination_file_id', route.get('destination'))
        if source is not None and int(source) != 0:
            change['source_file_id'] = int(source)
        if destination is not None and int(destination) != 0:
            change['destination_file_id'] = int(destination)
        if route.get('amount') is not None:
            change['amount'] = int(route['amount'])
        if route.get('fade') is not None:
            change['fade'] = int(route['fade'])
        if not change:
            continue
        if original is not None and _same_route(original[slot] if slot < len(original) else None, change):
            continue
        changes[slot] = change
    return changes


def apply_matrix_to_file(file_bytes, matrix):
    """Write the editor matrix into native .unosyp bytes, keeping everything else.

    Only routes that differ from the file's own decoded state are written, so
    untouched routes -- including the three that share bits with the sequencer
    -- keep their original bytes.
    """
    from matrix_codec import (write_matrix_to_file, decode_file_state, decode_matrix,
                              SEQUENCER_OVERLAP_SLOTS)
    original = decode_matrix(decode_file_state(file_bytes))
    original_routes = [{'source': r['source_file_id'], 'destination': r['destination_file_id'],
                        'amount': r['amount'], 'fade': r['fade']} for r in original]
    changes = matrix_routes_to_changes(matrix, original_routes)
    if not changes:
        return bytes(file_bytes)
    blocked = sorted(slot + 1 for slot in changes if slot + 1 in SEQUENCER_OVERLAP_SLOTS)
    if blocked:
        raise ValueError(
            f'Matrix routes {blocked} share bits with the sequencer length / Gate / Accent '
            f'fields and cannot be written yet')
    return write_matrix_to_file(file_bytes, changes, allow_overlapping=False)


def write_sequence_automation(sequence, matrix=None):
    """Build a native preset by editing resolved targets in its source bytes.

    ``matrix`` is the editor's modulation-matrix state.  It is applied to the
    state head first, then the sequencer fields are written last, because the
    matrix routes 5-7 share bits with the sequence length and the shared
    Gate/Accent values: the sequencer fields must win.
    """
    from uno_step_automation_decoder import write_resolved_values
    if not getattr(sequence, 'native_raw_hex', ''):
        raise ValueError('Native Save requires a preset loaded from a binary .unosyp file')
    raw = bytes.fromhex(sequence.native_raw_hex)
    if matrix is not None:
        raw = apply_matrix_to_file(raw, matrix)
    native = getattr(sequence, 'native_automation', {}) or {}
    entries = native.get('entries', [])
    resolved = {(int(item.get('step') or 0), item.get('parameter')) for item in entries
                if item.get('parameter') and item.get('step')}
    values = {}
    for item in entries:
        step = int(item.get('step') or 0)
        parameter = item.get('parameter')
        lane_name = PARAMETER_TO_LANE.get(parameter)
        if not lane_name or not 1 <= step <= 64:
            continue
        lane = next((line for line in sequence.automation
                     if line.get('parameter') == lane_name), None)
        lane_values = lane.get('values', []) if lane else []
        values[(step, parameter)] = lane_values[step - 1] if step <= len(lane_values) else None
    # A newly drawn point has no native Selection metadata and must not be
    # silently omitted from a supposedly native save.
    reverse = {lane: native_name for native_name, lane in PARAMETER_TO_LANE.items()}
    for lane in sequence.automation:
        parameter = reverse.get(lane.get('parameter'))
        if not parameter:
            continue
        for index, value in enumerate(lane.get('values', [])[:64], 1):
            if value is not None and (index, parameter) not in resolved:
                raise ValueError(f'Cannot add unresolved native target: Step {index} {parameter}')
    result = write_resolved_values(raw, values)
    result=encode_sequence_length(result, int(sequence.length))
    return encode_sequence_gate_accent(result, getattr(sequence,'gate_value',0), getattr(sequence,'accent_value',0))
