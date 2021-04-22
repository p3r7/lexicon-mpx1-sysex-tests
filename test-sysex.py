
import signal

import math
from functools import reduce # only in Python 3
import operator
import time

from pprint import pprint
from icecream import ic

import mido
# import mido.backends.pygame



## INIT - MIDI

mido.set_backend('mido.backends.pygame')

inport = mido.open_input('MidiSport 1x1 MIDI 1')
outport = mido.open_output('MidiSport 1x1 MIDI 1')

# outport.reset()

def cleanup_mido():
    inport.close()
    outport.close()

def handler(signum, frame):
    cleanup_mido()

signal.signal(signal.SIGHUP, handler)



## INIT - DEBUG

DEBUG = True

if DEBUG:
    ic.enable()
else:
    ic.disable()
ic.configureOutput(includeContext=True)



## CORE: DICTS

def getFromDict(dataDict, mapList):
    return reduce(operator.getitem, mapList, dataDict)

def setInDict(dataDict, mapList, value):
    getFromDict(dataDict, mapList[:-1])[mapList[-1]] = value



## CORE: BINARY ENCODING

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

def nibblize_str(v_str, size=None):
    v_arr = []
    for c in v_str:
       c_nibble = nibblize(ord(c))
       v_arr.append(c_nibble[0])
       v_arr.append(c_nibble[1])
    if size:
        while size > len(v_arr)/2:
            v_arr.append(0)
            v_arr.append(0)
        v_arr = v_arr[:size]
    return v_arr

def unnibblize(v_arr):
    v_arr = [hex(v)[2:] for v in reversed(v_arr)]
    v_hex_str = ''.join(v_arr)
    return int(v_hex_str, 16)

def unnibblize_str(v_arr):
    out = ""
    it=iter(v_arr)
    for v1, v2 in zip(it, it):
        v1 = hex(v1)[-1]
        v2 = hex(v2)[-1]
        v = v2 + v1
        out += chr(int(v, 16))
    return out

def nibble_fn_for_type(t):
    if t == 'int':
        nibble_fn = nibblize
    elif t == 'str':
        nibble_fn = nibblize_str
    else:
        nibble_fn = nibblize
    return nibble_fn

def unnibble_fn_for_type(t):
    if t == 'int':
        unnibble_fn = unnibblize
    elif t == 'str':
        unnibble_fn = unnibblize_str
    else:
        unnibble_fn = unnibblize
    return unnibble_fn



## API: DEVICE INQUIRY

# p12
# NB: 7F means all devices
def device_inquiry(inport, outport, device_id = 0x7f):
    payload = [0x7e, device_id, 0x06, 0x01]
    snd = mido.Message('sysex', data=payload)
    ic(snd.hex())
    outport.send(snd)
    time.sleep(0.01)
    rcv = inport.receive()
    ic(rcv.hex())
    rcv = rcv.bytes()
    return {
        'version_major': rcv[10],
        'version_minor': rcv[11],
        'version_dev_phase': rcv[12],
    }



## API - REQUEST
## generic interface defined p21

def request_by_control_levels(inport, outport, request_class, control_levels, device_id = 0x7f):
    rq_class_nibble = nibblize(request_class)

    nb_control_levels = len(control_levels)
    nb_cl_nibble = nibblize(nb_control_levels, 4)

    payload = [
        # header
        6,9,device_id,6,
        # request class:
        rq_class_nibble[0], rq_class_nibble[1],
    ]

    # nb of control levels (A-D = 4)
    # if nb_control_levels:
    for i in range(0,4):
        payload.append(nb_cl_nibble[i])

    for cl in control_levels:
        cl_nibble = nibblize(cl, 4)
        for i in range(0,4):
            payload.append(cl_nibble[i])

    snd = mido.Message('sysex', data=payload)
    ic(snd.hex())
    outport.send(snd)
    time.sleep(0.01)
    rcv = inport.receive()
    ic(rcv.hex())
    return rcv

def request_by_param_type(inport, outport, request_class, param_type, device_id = 0x7f):
    rq_class_nibble = nibblize(request_class)
    p_type_nibble = nibblize(param_type, 4)
    payload = [
        # header
        6,9,device_id,6,
        # request class:
        rq_class_nibble[0], rq_class_nibble[1],
        # param type (id)
        p_type_nibble[0], p_type_nibble[1], p_type_nibble[2], p_type_nibble[3],
    ]

    snd = mido.Message('sysex', data=payload)
    ic(snd.hex())
    outport.send(snd)
    time.sleep(0.01)
    rcv = inport.receive()
    ic(rcv.hex())
    return rcv

def request_by_effect(inport, outport, request_class, effect_type, effect_number, device_id = 0x7f):
    rq_class_nibble = nibblize(request_class)
    e_type_nibble = nibblize(effect_type)
    e_nb_nibble = nibblize(effect_number)
    payload = [
        # header
        6,9,device_id,6,
        # request class:
        rq_class_nibble[0], rq_class_nibble[1],
        # effect id / number
        e_type_nibble[0], e_type_nibble[1],
        e_nb_nibble[0], e_nb_nibble[1],
        # padding
        0, 0
    ]
    snd = mido.Message('sysex', data=payload)
    ic(snd.hex())
    outport.send(snd)
    time.sleep(0.01)
    rcv = inport.receive()
    ic(rcv.hex())
    return rcv

def request_by_program(inport, outport, request_class, program_number, device_id = 0x7f):
    rq_class_nibble = nibblize(request_class)
    p_nb_nibble = nibblize(program_number)
    payload = [
        # header
        6,9,device_id,6,
        # request class:
        rq_class_nibble[0], rq_class_nibble[1],
        # program number
        p_nb_nibble[0], p_nb_nibble[1],
        # padding
        0, 0
    ]
    snd = mido.Message('sysex', data=payload)
    outport.send(snd)
    ic(snd.hex())
    time.sleep(0.01)
    rcv = inport.receive()
    ic(rcv.hex())
    return rcv

# p13
def get_system_config(inport, outport, device_id = 0x7f):
    rcv = request_by_control_levels(inport, outport, 0, [], device_id)
    rcv = rcv.bytes()
    return {
        'version_major': unnibblize(rcv[5:7]),
        'version_minor': unnibblize(rcv[7:9]),
        'time': unnibblize_str(rcv[9:25]),
        'date': unnibblize_str(rcv[25:47]),
        'nb_params': unnibblize(rcv[47:51]),
        'bottom_param': unnibblize(rcv[51:55]),
        'max_control_levels': unnibblize(rcv[55:59]),
    }

## p14
def get_param_data(inport, outport, control_levels, value_type = 'int', device_id = 0x7f):
    rcv = request_by_control_levels(inport, outport, 1, control_levels, device_id)
    rcv = rcv.bytes()
    size_bytes = unnibblize(rcv[5:9])
    nb_control_levels = unnibblize(rcv[(9+2*size_bytes):(9+2*size_bytes)+4])
    control_levels = []
    cl_start_b = (9+2*size_bytes)+4
    for i in range(0, nb_control_levels):
        start_b = cl_start_b+(i*4)
        control_levels.append(unnibblize(rcv[start_b:start_b+4]))

    v_parse_fn = unnibble_fn_for_type(value_type)

    return {
        # 'size_bytes': size_bytes,
        # 'nb_control_levels': nb_control_levels,
        'value': v_parse_fn(rcv[9:(9+2*size_bytes)]),
        'control_levels': control_levels,
    }

## p16
def get_param_display(inport, outport, control_levels, device_id = 0x7f):
    rcv = request_by_control_levels(inport, outport, 2, control_levels, device_id)
    rcv = rcv.bytes()
    size_bytes = unnibblize(rcv[5:9])
    return unnibblize_str(rcv[9:(9+2*size_bytes)])

## p17
def get_param_type(inport, outport, control_levels, device_id = 0x7f):
    rcv = request_by_control_levels(inport, outport, 3, control_levels, device_id)
    rcv = rcv.bytes()
    return unnibblize(rcv[5:9])

## p18
def get_param_desc(inport, outport, param_type, device_id = 0x7f):
    rcv = request_by_param_type(inport, outport, 4, param_type, device_id)
    rcv = rcv.bytes()

    p_type = unnibblize(rcv[5:9])

    size_chars_label = unnibblize(rcv[9:11])
    label = unnibblize_str(rcv[11:(11+2*size_chars_label)])
    p = (11+2*size_chars_label)

    bs=2
    size_bytes = unnibblize(rcv[p:p+(2*bs)])
    p += (2*bs)

    bs=1
    control_flags = unnibblize(rcv[p:p+(2*bs)])
    p += (2*bs)

    bs=2
    option_p_type = unnibblize(rcv[p:p+(2*bs)])
    p += (2*bs)

    bs=1
    nb_units_per_limit = unnibblize(rcv[p:p+(2*bs)])
    p += (2*bs)

    rcv = rcv[p:]
    vals = []
    nb_vals = math.floor(len(rcv)/(3*2*2)) # NB: this is hackish
    for i in range(0, nb_vals):
        vals.append({
            'min': unnibblize(rcv[i*(3*2*2):i*(3*2*2)+4]),
            'max': unnibblize(rcv[i*(3*2*2)+4:i*(3*2*2)+8]),
            'display_unit': unnibblize(rcv[i*(3*2*2)+8:i*(3*2*2)+12]),
        })

    return {
        'param_type': p_type,
        'label': label,
        'param_size': size_bytes,
        'control_flags': control_flags,
        'option_param_type': option_p_type,
        'nb_units_per_limit': nb_units_per_limit,
        'vals': vals,
    }

## Same as `get_param_desc` but returns only the label
## p20
def get_param_label(inport, outport, control_levels, device_id = 0x7f):
    rcv = request_by_control_levels(inport, outport, 5, control_levels, device_id)
    rcv = rcv.bytes()
    size_chars = unnibblize(rcv[5:9])
    return {
        'label': unnibblize_str(rcv[9:(9+2*size_chars)]),
    }

# p24
# List all parameter types (aka param numbers) for a given effect
def get_effect_params(inport, outport, effect_type, effect_number, device_id = 0x7f):
    rcv = request_by_effect(inport, outport, 0x18, effect_type, effect_number, device_id)
    rcv = rcv.bytes()

    label = unnibblize_str(rcv[9:31])
    nb_params = unnibblize(rcv[31:33])
    rcv = rcv[33:]
    params = []
    for i in range(0, nb_params):
        params.append(unnibblize(rcv[i*4:i*4+4]))
    return {
        'label': label,
        'params': params,
    }

# p36
def get_program_info(inport, outport, program_number, device_id = 0x7f):
    rcv = request_by_program(inport, outport, 0x1a, program_number, device_id)
    rcv = rcv.bytes()

    return {
        'program_number': unnibblize(rcv[5:9]),
        'label': unnibblize_str(rcv[9:33]),
        'pitch_effect_nb': unnibblize(rcv[33:35]),
        'chorus_effect_nb': unnibblize(rcv[35:37]),
        'eq_effect_nb': unnibblize(rcv[37:39]),
        'mod_effect_nb': unnibblize(rcv[39:41]),
        'reverb_effect_nb': unnibblize(rcv[41:43]),
        'delay_effect_nb': unnibblize(rcv[43:45]),
    }



## API - DATA TRANSFER

# p14
def set_param_data(outport, control_levels, size_bytes, v, value_type = 'int', device_id = 0x7f):
    size_b_nibble = nibblize(size_bytes, 4)

    # if value_type == 'str':
    size_bytes *= 2

    v_nibble_fn = nibble_fn_for_type(value_type)
    v_nibble = v_nibble_fn(v, size_bytes)

    payload = [6,9,device_id,1,
               # value size
               size_b_nibble[0],size_b_nibble[1],size_b_nibble[2],size_b_nibble[3]]
    for v_b in v_nibble:
        payload.append(v_b)

    nb_control_levels = len(control_levels)
    nb_cl_nibble = nibblize(nb_control_levels, 4)
    for i in range(0, 4):
        payload.append(nb_cl_nibble[i])
    for cl in control_levels:
        cl_nibble = nibblize(cl, 4)
        for i in range(0,4):
            payload.append(cl_nibble[i])

    snd = mido.Message('sysex', data=payload)
    ic(snd.hex())
    outport.send(snd)
    time.sleep(0.01)



## API - DUMPS

## page 23
def db_dump(inport, outport, device_id = 0x7f):
    payload = [0x06, 0x09, device_id, 0x06, 0x06, 0x01,
               0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    snd = mido.Message('sysex', data=payload)
    ic(snd.hex())
    outport.send(snd)
    rcv = inport.receive()
    ic(rcv.hex())
    rcv = rcv.bytes()
    rcv_payload = rcv[5:]
    out = []
    nb_programs = math.floor(len(rcv_payload)/6) # NB: this is hackish
    for i in range(0, nb_programs):
        out.append({
            'effect_type': unnibblize(rcv_payload[(i*(4+2)):i*(4+2)+4]),
            'source_type': unnibblize(rcv_payload[i*(4+2)+4:i*(4+2)+6]),
        })
    return out



## API - SPECIFIC - CURRENT PROGRAM

def get_current_program(inport, outport, device_id = 0x7f):
    return get_param_data(inport, outport, [0, 19, 9], 'int', device_id)


def set_current_program(outport, v, device_id = 0x7f):
    return set_param_data(outport, [0, 19, 9], 2, v, 'int', device_id)




## API - SPECIFIC - DISPLAY

def display_dump(inport, outport, device_id = 0x7f):
    return get_param_data(inport, outport, [1, 8, 1], 'str', device_id)

def set_display(outport, message, device_id = 0x7f):
    length = 32
    set_param_data(outport, [1, 8, 1], length, message, 'str', device_id)

def dump_custom_characters(inport, outport, device_id = 0x7f):
    return get_param_data(inport, outport, [1, 8, 3], 'str', device_id)



## BUILD CONTROL TREE

# p5
def make_control_tree(inport, outport, device_id = 0x7f, control_level=[], max_cl_depth=5):

    print("------------------------")
    pprint(control_level)

    p_type = get_param_type(inport, outport, control_level, device_id)
    p_desc = get_param_desc(inport, outport, p_type, device_id)
    p = {
        'type': p_type,
        'desc': p_desc,
    }

    print(p_desc['label'])

    # non-editable param, i.e. tree branching
    if p_desc['control_flags'] & 0x04 != 0 \
       and len(control_level)+1 <= max_cl_depth \
       and not (p_desc['label'] in ['CC        ', 'Cont Remap ', 'Ctl Smooth', 'Map        ', 'ProgramDump']):
        print('BRANCH!')
        p['children'] = {}
        for v in p_desc['vals']:
            for cl_id in range(v['min'], v['max']+1):
                cl = control_level.copy()
                cl.append(cl_id)
                branch = make_control_tree(inport, outport, device_id, cl)
                p['children'][cl_id] = branch
    return p



## SPECIFIC ACCESS

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

def update_master_mix(outport, v, device_id = 0x7f):
    v_nibble = nibblize(v)
    payload = [6,9,device_id,1,1,0,0,0,v_nibble[0],v_nibble[1],3,0,0,0,0,0,0,0,3,1,0,0,12,0,0,0]
    snd = mido.Message('sysex', data=payload)
    print(snd.hex())
    outport.send(snd)

def update_master_level(outport, v, device_id = 0x7f):
    v_nibble = nibblize(v)
    payload = [6,9,device_id,1,1,0,0,0,v_nibble[0],v_nibble[1],3,0,0,0,0,0,0,0,3,1,0,0,13,0,0,0]
    snd = mido.Message('sysex', data=payload)
    outport.send(snd)

def update_master_mix2(outport, v, device_id = 0x7f):
    set_param_data(outport, [0, 19, 12], 1, v, 'int', device_id)




## TESTS

resp = device_inquiry(inport, outport, 0x00)
# resp = db_dump(inport, outport, 0x00)


# update_master_mix(outport, 100, 0x00)
# update_master_mix2(outport, 100, 0x00)
# update_master_level(outport, -4, 0x00)
# resp = get_param_eq_m_gain(inport, outport, 0x00)

# resp = display_dump(inport, outport, 0x00)


# resp = get_param_display(inport, outport, [0, 2, 1, 2], 0x00)
# p_type = get_param_type(inport, outport, [0, 2, 1, 2], 0x00)
# resp = get_param_desc(inport, outport, p_type, 0x00)
# resp = get_param_label(inport, outport, [0, 2, 1, 2], 0x00)

# resp = get_system_config(inport, outport, 0x00)

# p_type = get_param_type(inport, outport, [0, 19, 9], 0x00)
# print(p_type)
# resp = get_param_desc(inport, outport, p_type, 0x00)

# resp = request_by_control_levels(inport, outport, 0, [1], 0x00)

# resp = get_effect_params(inport, outport, 1, 1, 0x00)

# resp = get_program_info(inport, outport, 0, 0x00)

# resp = get_param_data(inport, outport, [0, 19, 9], device_id = 0x00)
# set_current_program(outport, 44, device_id = 0x00)
resp = get_current_program(inport, outport, device_id = 0x00)

# pprint(p_type)
# pprint(resp)


# p_type = get_param_type(inport, outport, [1, 2, 5], 0x00)
# p_type = get_param_type(inport, outport, [0, 18, 9, 1], 0x00)
# resp = get_param_desc(inport, outport, p_type, 0x00)
pprint(resp)


# display
# p_type = get_param_type(inport, outport, [1, 8, 1], 0x00)
# print(p_type)
# resp = get_param_desc(inport, outport, 0x011e , 0x00)
# pprint(resp)

# mix
# p_type = get_param_type(inport, outport, [0, 19, 12], 0x00)
# resp = get_param_desc(inport, outport, 327 , 0x00)
# print(resp)

# cutom characters
# p_type = get_param_type(inport, outport, [1, 8, 3], 0x00)
# p_type = 0x0130
# resp = get_param_desc(inport, outport, p_type, 0x00)
# print(resp)

# resp = dump_custom_characters(inport, outport, 0x00)
# pprint(resp)

# try:
#     display_dump(inport, outport, 0x00)
#     # set_display(outport, " / / / /", 0x00)
#     # all custom characters:
#     set_display(outport, ""+chr(0)+chr(1)+chr(2)+chr(3)+chr(4)+chr(5)+chr(6)+chr(7), 0x00)
# except KeyboardInterrupt as e:
#     cleanup_mido()


## MAIN

device_id = 0x00

# 1- get number of parameters
# sysconf = get_system_config(inport, outport, device_id)
# pprint(sysconf)
# nb_params = sysconf['nb_params']


# 2- build control tree

# 2-1- db of all param desc by param type (aka param number)
# NB: this is slow AF
# p_type_desc_map={}
# for p_type in range(0, nb_params):
#     p_desc = get_param_desc(inport, outport, p_type, device_id)
#     p_type_desc_map[p_type] = p_desc

# 2-1- actual control tree
# root_p_type = get_param_type(inport, outport, [], device_id)
# root_p_desc = p_type_desc_map[root_p_type]
# root_p_desc = get_param_desc(inport, outport, 1, device_id)

# pprint(root_p_type)

# TODO: test that is not editable param -> tree branching
# for cl_id in range(root_p_desc['vals'][0]['min'], root_p_desc['vals'][0]['max']+1):
#     p_type = get_param_type(inport, outport, [cl_id], device_id)
#     p_desc = get_param_desc(inport, outport, p_type, device_id)
#     print("------------------")
#     pprint(p_desc)


# try:
#     # NB: this is slow AF
#     control_tree = make_control_tree(inport, outport, 0x00)
#     pprint(control_tree['desc']['label'])
#     pprint(control_tree['children'][0]['desc']['label'])
#     pprint(control_tree['children'][0]['children'][2]['desc']['label'])
#     pprint(control_tree['children'][0]['children'][2]['children'][1]['desc']['label'])
#     pprint(control_tree['children'][0]['children'][2]['children'][1]['children'][2]['desc']['label'])

#     # print(control_tree[0]['label'])
#     # print(control_tree[0]['children'][2]['label'])
#     # print(control_tree[0]['children'][2]['children'][1]['label'])
#     # print(control_tree[0]['children'][2]['children'][1]['children'][2]['label'])
#     # pprint(control_tree)
# except KeyboardInterrupt as e:
#     cleanup_mido()



# pprint(root_p_desc)


## CLEANUP

cleanup_mido()
