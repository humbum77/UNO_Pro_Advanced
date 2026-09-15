"""Read-only confirmed container. Does not infer entry IDs, values or steps."""
def read_automation(data):
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
