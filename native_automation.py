"""Read-only Step Automation decoding and shared Sequence lane integration."""

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
         'step': item.get('step', native.get('step'))}
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
