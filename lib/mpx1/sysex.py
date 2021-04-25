
import math
import time

from pprint import pprint
from icecream import ic

import mido

from lib.core.binencoding import nibblize, nibblize_str, \
    unnibblize, unnibblize_str, \
    decode_negative_maybe, \
    nibble_fn_for_type, unnibble_fn_for_type



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



## API - REQUEST (GENERIC)
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



## API - REQUEST - SYSTEM

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



## API - PROGRAMS

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

def get_current_program(inport, outport, device_id = 0x7f):
    return get_param_data(inport, outport, [0, 19, 9], 'int', device_id)

def set_current_program(outport, v, device_id = 0x7f):
    set_param_data(outport, [0, 19, 9], 2, v, 'int', device_id)

# ## NB: on v1.10, we need to do a get call otherwise cache would not get updated
# ## -> might be a MIDI buffer issue w/ mido as well
# def set_current_program_safe(inport, outport, v, device_id = 0x7f):
#     set_current_program(outport, v, device_id)
#     get_current_program(inport, outport, device_id)

# p36
def get_program_info(inport, outport, program_number, device_id = 0x7f):
    rcv = request_by_program(inport, outport, 0x1a, program_number, device_id)
    rcv = rcv.bytes()

    return {
        'program_number': unnibblize(rcv[5:9]),
        'label': unnibblize_str(rcv[9:33]),
        'algos': [
            unnibblize(rcv[33:35]), # Pitch
            unnibblize(rcv[35:37]), # Chorus
            unnibblize(rcv[37:39]), # EQ
            unnibblize(rcv[39:41]), # Mod
            unnibblize(rcv[41:43]), # Reverb
            unnibblize(rcv[43:45]), # Delay
        ]
    }



## API - EFFECTS

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



## API - PARAMS

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
            # 'min': decode_negative_maybe(unnibblize(rcv[i*(3*2*2):i*(3*2*2)+4])),
            # 'max': decode_negative_maybe(unnibblize(rcv[i*(3*2*2)+4:i*(3*2*2)+8])),
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



## API - HW - DISPLAY

def display_dump(inport, outport, device_id = 0x7f):
    return get_param_data(inport, outport, [1, 8, 1], 'str', device_id)

def set_display(outport, message, device_id = 0x7f):
    length = 32
    set_param_data(outport, [1, 8, 1], length, message, 'str', device_id)

def dump_custom_characters(inport, outport, device_id = 0x7f):
    return get_param_data(inport, outport, [1, 8, 3], 'str', device_id)

def set_display_all_special_chars(outport, device_id  = 0x7f):
    set_display(outport, ""+chr(0)+chr(1)+chr(2)+chr(3)+chr(4)+chr(5)+chr(6)+chr(7), device_id)
