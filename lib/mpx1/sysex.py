
import math
import time

from pprint import pprint
from icecream import ic

import mido

from lib.core.binencoding import nibblize, nibblize_str, \
    unnibblize, unnibblize_str, \
    decode_negative_maybe, \
    nibble_fn_for_type, unnibble_fn_for_type



## CONF

SYNC_RQ_WAIT=0.01



## API: DEVICE INQUIRY

# p12
# NB: 7F means all devices
def device_inquiry(inport, outport, device_id = 0x7f, sync=True):
    payload = [0x7e, device_id, 0x06, 0x01]
    snd = mido.Message('sysex', data=payload)
    ic(snd.hex())
    outport.send(snd)
    if sync:
        time.sleep(SYNC_RQ_WAIT)
        rcv = inport.receive()
        ic(rcv.hex())
        return parse_device_inquiry_resp(rcv.bytes())

def is_device_inquiry_resp(rcv_bytes, device_id=0x7f):
    # Each line:
    # - SySex header
    # - Universal System Exclusive Non-real time header
    # - Device id
    # - General Information (sub-ID#1)
    # - Identity Reply (sub-ID#1)
    # - Lexicon SySex id code
    # - Device Family Code
    # - Device Family Member Code (MPX1)
    return  rcv_bytes[0] == 0xf0 \
        and rcv_bytes[1] == 0x7e \
        and (device_id == 0x7f or rcv_bytes[2] == device_id) \
        and rcv_bytes[3] == 0x06 \
        and rcv_bytes[4] == 0x02 \
        and rcv_bytes[5] == 0x06 \
        and rcv_bytes[6] == 0x00 and rcv_bytes[7] == 0x00 \
        and rcv_bytes[8] == 0x09 and rcv_bytes[9] == 0x00

def parse_device_inquiry_resp(rcv_bytes):
    return {
        'version_major': rcv_bytes[10],
        'version_minor': rcv_bytes[11],
        'version_dev_phase': rcv_bytes[12],
    }



## API - REQUEST (GENERIC)
## generic interface defined p21

def request_by_control_levels(inport, outport, request_class, control_levels, device_id = 0x7f, sync=True):
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

    if sync:
        time.sleep(SYNC_RQ_WAIT)
        rcv = inport.receive()
        ic(rcv.hex())
        return rcv

def request_by_param_type(inport, outport, request_class, param_type, device_id = 0x7f, sync=True):
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
    if sync:
        time.sleep(SYNC_RQ_WAIT)
        rcv = inport.receive()
        ic(rcv.hex())
        return rcv

def request_by_effect(inport, outport, request_class, effect_type, effect_number, device_id = 0x7f, sync=True):
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
    if sync:
        time.sleep(SYNC_RQ_WAIT)
        rcv = inport.receive()
        ic(rcv.hex())
        return rcv

def request_by_program(inport, outport, request_class, program_number, device_id = 0x7f, sync=True):
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
    if sync:
        time.sleep(SYNC_RQ_WAIT)
        rcv = inport.receive()
        ic(rcv.hex())
        return rcv

def is_mpx_resp_with_class(rcv_bytes, sysex_class, device_id=0x7f):
    # Each line:
    # - SySex header
    # - Lexicon SySex id code
    # - Device Family Member Code (MPX1)
    # - Device id
    # - Class
    return  rcv_bytes[0] == 0xf0 \
        and rcv_bytes[1] == 0x06 \
        and rcv_bytes[2] == 0x09 \
        and (device_id == 0x7f or rcv_bytes[3] == device_id) \
        and rcv_bytes[4] == sysex_class



## API - REQUEST - SYSTEM

# p13
def get_system_config(inport, outport, device_id = 0x7f, sync=True):
    rcv = request_by_control_levels(inport, outport, 0, [], device_id, sync)
    if sync:
        return parse_system_config_resp(rcv.bytes())

def is_system_config_resp(rcv_bytes, device_id=0x7f):
    return is_mpx_resp_with_class(rcv_bytes, 0x00, device_id)

def parse_system_config_resp(rcv_bytes):
    return {
        'version_major': unnibblize(rcv_bytes[5:7]),
        'version_minor': unnibblize(rcv_bytes[7:9]),
        'time': unnibblize_str(rcv_bytes[9:25]),
        'date': unnibblize_str(rcv_bytes[25:47]),
        'nb_params': unnibblize(rcv_bytes[47:51]),
        'bottom_param': unnibblize(rcv_bytes[51:55]),
        'max_control_levels': unnibblize(rcv_bytes[55:59]),
    }


## API - PROGRAMS

## page 23
def db_dump(inport, outport, device_id = 0x7f, sync=True):
    payload = [0x06, 0x09, device_id, 0x06, 0x06, 0x01,
               0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    snd = mido.Message('sysex', data=payload)
    ic(snd.hex())
    outport.send(snd)
    if sync:
        time.sleep(SYNC_RQ_WAIT)
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

def get_current_program(inport, outport, device_id = 0x7f, sync=True):
    return get_param_data(inport, outport, [0, 19, 9], 'int', device_id, sync)

def set_current_program(outport, v, device_id = 0x7f):
    set_param_data(outport, [0, 19, 9], 2, v, 'int', device_id)

def is_change_program_msg(rcv_bytes, value_type, device_id = 0x7f):
    if not is_param_data_resp(rcv_bytes, device_id):
        return False
    return get_param_data_resp_cl(rcv_bytes) == [0, 19, 9]


# ## NB: on v1.10, we need to do a get call otherwise cache would not get updated
# ## -> might be a MIDI buffer issue w/ mido as well
# def set_current_program_safe(inport, outport, v, device_id = 0x7f):
#     set_current_program(outport, v, device_id)
#     get_current_program(inport, outport, device_id)

# p36
def get_program_info(inport, outport, program_number, device_id = 0x7f, sync=True):
    rcv = request_by_program(inport, outport, 0x1a, program_number, device_id, sync)

    if sync:
        return parse_program_info_resp(rcv.bytes())

def is_program_info_resp(rcv_bytes, device_id=0x7f):
    return is_mpx_resp_with_class(rcv_bytes, 0x1a, device_id)

def parse_program_info_resp(rcv_bytes):
        return {
            'program_number': unnibblize(rcv_bytes[5:9]),
            'label': unnibblize_str(rcv_bytes[9:33]),
            'algos': [
                unnibblize(rcv_bytes[33:35]), # Pitch
                unnibblize(rcv_bytes[35:37]), # Chorus
                unnibblize(rcv_bytes[37:39]), # EQ
                unnibblize(rcv_bytes[39:41]), # Mod
                unnibblize(rcv_bytes[41:43]), # Reverb
                unnibblize(rcv_bytes[43:45]), # Delay
            ]
        }

## Up to 10 macro parameters (0..9) accessible
def get_current_program_macro(inport, outport, macro_id, device_id = 0x7f, sync=True):
    effect_id = get_param_data(inport, outport, [0, 18, macro_id, 0], 'int', device_id)['value']
    param_id = get_param_data(inport, outport, [0, 18, macro_id, 1], 'int', device_id)['value']
    return {
        'effect_id': effect_id,
        'param_id': param_id,
    }

def get_current_program_macros(inport, outport, device_id = 0x7f, sync=True):
    out = []
    for i in range(0, 10):
        v = get_current_program_macro(inport, outport, i, device_id, sync)
        if sync:
            if v['param_id'] == 255: # unassigned
                break
            out.append(v)
    if sync:
        return out

def get_current_program_context(inport, outport, device_id = 0x7f, control_tree=None):
    curr_p_data = get_current_program(inport, outport, device_id)
    curr_p_id = curr_p_data['value']
    curr_p_info = get_program_info(inport, outport, curr_p_id, device_id)
    curr_p_soft_params = get_current_program_macros(inport, outport, device_id)
    macros = []
    for sp in curr_p_soft_params:
        param_id = sp['param_id']

        effect_id = sp['effect_id']
        effect_cl = [0, effect_id]

        if effect_id < 6: # effect param
            algo_id = curr_p_info['algos'][effect_id]
            param_cl = [0, effect_id, algo_id, param_id]
        else: # not actually an effect but a modulation source
            param_cl = [0, effect_id, param_id]

        if control_tree is not None:
            effect_p_type = control_tree['cl->type'][tuple(effect_cl)]
            effect_label = control_tree['descs'][effect_p_type]['label'].strip()
            param_type = control_tree['cl->type'][tuple(param_cl)]
            param_desc = control_tree['descs'][param_type]
        else:
            effect_label = get_param_label(inport, outport, effect_cl, device_id)['label'].strip()
            param_type = get_param_type(inport, outport, param_cl, device_id)
            param_desc = get_param_desc(inport, outport, param_type, device_id)

        param_data = get_param_data(inport, outport, param_cl, device_id=device_id)
        macros.append({
            'type': param_type,
            'cl': param_cl,
            'label': effect_label + " " + param_desc['label'],
            'desc': param_desc,
            'value': param_data,
        })

    return {
        'pgm_id': curr_p_info['label'],
        'soft_params': macros,
    }




## API - EFFECTS

# p24
# List all parameter types (aka param numbers) for a given effect
def get_effect_params(inport, outport, effect_type, effect_number, device_id = 0x7f, sync=True):
    rcv = request_by_effect(inport, outport, 0x18, effect_type, effect_number, device_id, sync)
    if sync:
        return parse_effects_params_resp(rcv.bytes())

def is_effects_params_resp(rcv_bytes, device_id=0x7f):
    return is_mpx_resp_with_class(rcv_bytes, 0x18, device_id)

def parse_effects_params_resp(rcv_bytes):
    label = unnibblize_str(rcv_bytes[9:31])
    nb_params = unnibblize(rcv_bytes[31:33])
    rcv_bytes = rcv_bytes[33:]
    params = []
    for i in range(0, nb_params):
        params.append(unnibblize(rcv_bytes[i*4:i*4+4]))
    return {
        'label': label,
        'params': params,
    }



## API - PARAMS

## p14
def get_param_data(inport, outport, control_levels, value_type = 'int', device_id = 0x7f, sync=True):
    rcv = request_by_control_levels(inport, outport, 0x01, control_levels, device_id, sync)
    if sync:
        return parse_param_data_resp(rcv.bytes(), value_type)

def is_param_data_resp(rcv_bytes, device_id=0x7f):
    return is_mpx_resp_with_class(rcv_bytes, 0x01, device_id)

def parse_param_data_resp(rcv_bytes, value_type):
    control_levels = get_param_data_resp_cl(rcv_bytes)
    size_bytes = unnibblize(rcv_bytes[5:9])
    v_parse_fn = unnibble_fn_for_type(value_type)
    v = v_parse_fn(rcv_bytes[9:(9+2*size_bytes)])
    return {
        # 'size_bytes': size_bytes,
        'value': v,
        'control_levels': control_levels,
    }

def get_param_data_resp_cl(rcv_bytes):
    size_bytes = unnibblize(rcv_bytes[5:9])
    nb_control_levels = unnibblize(rcv_bytes[(9+2*size_bytes):(9+2*size_bytes)+4])
    control_levels = []
    cl_start_b = (9+2*size_bytes)+4
    for i in range(0, nb_control_levels):
        start_b = cl_start_b+(i*4)
        control_levels.append(unnibblize(rcv_bytes[start_b:start_b+4]))
    return control_levels

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

## p16
def get_param_display(inport, outport, control_levels, device_id = 0x7f, sync=True):
    rcv = request_by_control_levels(inport, outport, 0x02, control_levels, device_id, sync)
    if sync:
        rcv = rcv.bytes()
        size_bytes = unnibblize(rcv[5:9])
        return unnibblize_str(rcv[9:(9+2*size_bytes)])

def is_param_display_resp(rcv_bytes, device_id=0x7f):
    return is_mpx_resp_with_class(rcv_bytes, 0x02, device_id)

## p17
def get_param_type(inport, outport, control_levels, device_id = 0x7f, sync=True):
    rcv = request_by_control_levels(inport, outport, 0x03, control_levels, device_id)
    if sync:
        rcv = rcv.bytes()
        return unnibblize(rcv[5:9])

def is_param_type_resp(rcv_bytes, device_id=0x7f):
    return is_mpx_resp_with_class(rcv_bytes, 0x03, device_id)

## p18
def get_param_desc(inport, outport, param_type, device_id = 0x7f, sync=True):
    rcv = request_by_param_type(inport, outport, 0x04, param_type, device_id, sync)
    if sync:
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

def is_param_desc_resp(rcv_bytes, device_id=0x7f):
    return is_mpx_resp_with_class(rcv_bytes, 0x04, device_id)

## Same as `get_param_desc` but returns only the label
## p20
def get_param_label(inport, outport, control_levels, device_id = 0x7f, sync=True):
    rcv = request_by_control_levels(inport, outport, 0x05, control_levels, device_id)
    if sync:
        rcv = rcv.bytes()
        size_chars = unnibblize(rcv[5:9])
        return {
            'label': unnibblize_str(rcv[9:(9+2*size_chars)]),
        }

def is_param_label_resp(rcv_bytes, device_id=0x7f):
    return is_mpx_resp_with_class(rcv_bytes, 0x05, device_id)



## API - HW - DISPLAY

def display_dump(inport, outport, device_id = 0x7f, sync=True):
    return get_param_data(inport, outport, [1, 8, 1], 'str', device_id, sync)

def set_display(outport, message, device_id = 0x7f):
    length = 32
    set_param_data(outport, [1, 8, 1], length, message, 'str', device_id)

def dump_custom_characters(inport, outport, device_id = 0x7f, sync=True):
    return get_param_data(inport, outport, [1, 8, 3], 'str', device_id, sync)

def set_display_all_special_chars(outport, device_id  = 0x7f):
    set_display(outport, ""+chr(0)+chr(1)+chr(2)+chr(3)+chr(4)+chr(5)+chr(6)+chr(7), device_id)
