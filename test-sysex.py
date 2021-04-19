import mido
# import mido.backends.pygame
from pprint import pprint



## INIT

mido.set_backend('mido.backends.pygame')

inport = mido.open_input('MidiSport 1x1 MIDI 1')
outport = mido.open_output('MidiSport 1x1 MIDI 1')



## FNS

def neg_complement_maybe(v):
    if v<0:
        return 256 + v
    return v

def nibblize(v, size=2):
    v = neg_complement_maybe(v)
    v_str = hex(v)[2:]
    v_arr = [int(v, 16) for v in reversed(v_str)]
    while len(v_arr) < size:
        v_arr.append(0)
    return v_arr

    # if len(v_str) == 1:
    #     return [int(v_str[0], 16), 0]
    # else:
    #     return [int(v_str[1], 16), int(v_str[0], 16)]

def unnibblize(v_arr):
    v_arr = [hex(v)[2:] for v in reversed(v_arr)]
    v_hex_str = ''.join(v_arr)
    return int(v_hex_str, 16)

# NB: 7F means all devices
def device_inquiry(inport, outport, device_id = 0x7f):
    payload = [0x7e, device_id, 0x06, 0x01]
    snd = mido.Message('sysex', data=payload)
    outport.send(snd)
    rcv = inport.receive()
    rcv = rcv.bytes()
    return {
        'version_major': rcv[10],
        'version_minor': rcv[11],
        'version_dev_phase': rcv[12],
    }

## NB: not working
def db_dump(inport, outport, device_id = 0x7f):
    payload = [0x06, 0x09, device_id, 0x06, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ]
    snd = mido.Message('sysex', data=payload)
    # print(snd.hex())
    outport.send(snd)
    rcv = inport.receive()
    print(rcv.hex())


def update_master_mix(outport, v, device_id = 0x7f):
    v_nibble = nibblize(v)
    payload = [6,9,device_id,1,1,0,0,0,v_nibble[0],v_nibble[1],3,0,0,0,0,0,0,0,3,1,0,0,12,0,0,0]
    snd = mido.Message('sysex', data=payload)
    outport.send(snd)

def update_master_level(outport, v, device_id = 0x7f):
    v_nibble = nibblize(v)
    payload = [6,9,device_id,1,1,0,0,0,v_nibble[0],v_nibble[1],3,0,0,0,0,0,0,0,3,1,0,0,13,0,0,0]
    snd = mido.Message('sysex', data=payload)
    outport.send(snd)

def display_dump(inport, outport, device_id = 0x7f):
    return get_param_data(inport, outport, [1, 8, 1], device_id)


def get_param_eq_m_gain(inport, outport, device_id = 0x7f):
    control_levels = [
        # level A - Program
        0,
        # level B - EQ
        2,
        # level C - EQ algo: (M)
        1,
        # level D - Param: Gain
        2
    ]
    return get_param_data(inport, outport, control_levels, device_id)

def get_param_data(inport, outport, control_levels, device_id = 0x7f):
    rcv = get_request(inport, outport, 1, control_levels, device_id)
    # print(rcv.hex())
    rcv = rcv.bytes()
    size_bytes = unnibblize(rcv[5:9])
    nb_control_levels = unnibblize(rcv[(9+2*size_bytes):(9+2*size_bytes)+4])
    control_levels = []
    cl_start_b = (9+2*size_bytes)+4
    for i in range(0, nb_control_levels):
        start_b = cl_start_b+(i*4)
        control_levels.append(unnibblize(rcv[start_b:start_b+4]))
    return {
        # 'size_bytes': size_bytes,
        # 'nb_control_levels': nb_control_levels,
        'value': unnibblize(rcv[9:(9+2*size_bytes)]),
        'control_levels': control_levels,
    }


def get_param_display(inport, outport, control_levels, device_id = 0x7f):
    nb_control_levels = len(control_levels)
    nb_cl_nibble = nibblize(nb_control_levels, 4)
    get_request(inport, outport, 2, control_levels, device_id)


def get_request(inport, outport, request_class, control_levels, device_id = 0x7f):
    rq_class_nibble = nibblize(request_class)

    nb_control_levels = len(control_levels)
    nb_cl_nibble = nibblize(nb_control_levels, 4)

    payload = [
        # header
        6,9,device_id,6,
        # request class:
        rq_class_nibble[0],rq_class_nibble[1],
        # nb of control levels (A-D = 4)
        nb_cl_nibble[0], nb_cl_nibble[1], nb_cl_nibble[2], nb_cl_nibble[3]]

    for cl in control_levels:
        cl_nibble = nibblize(cl, 4)
        for i in range(0,4):
            payload.append(cl_nibble[i])

    snd = mido.Message('sysex', data=payload)
    outport.send(snd)
    rcv = inport.receive()
    print(rcv.hex())
    return rcv


## MAIN

# resp = device_inquiry(inport, outport, 0x00)
# resp = db_dump(inport, outport, 0x00)

# update_master_mix(outport, 100, 0x00)
# update_master_level(outport, -4, 0x00)
resp = get_param_eq_m_gain(inport, outport, 0x00)

# resp = display_dump(inport, outport, 0x00)

pprint(resp)

# get_param_display(inport, outport, [0, 2, 1, 2], 0x00)


## CLEANUP

inport.close()
# outport.reset()
outport.close()
