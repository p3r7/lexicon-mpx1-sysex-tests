
from pprint import pprint

import lib.mpx1.sysex as mpx1_sysex


## GLOBAL PARAMS

def update_master_mix(outport, v, device_id = 0x7f):
    mpx1_sysex.set_param_data(outport, [0, 19, 12], 1, v, 'int', device_id)

def update_master_level(outport, v, device_id = 0x7f):
    mpx1_sysex.set_param_data(outport, [0, 19, 13], 1, v, 'int', device_id)



## CURRENT PROGRAM MACRO PARAMS (SOFT ROW)

## Up to 10 macro parameters (0..9) accessible
def get_current_program_macro(inport, outport, macro_id, device_id = 0x7f):
   effect_id = mpx1_sysex.get_param_data(inport, outport, [0, 18, macro_id, 0], 'int', device_id)['value']
   param_id = mpx1_sysex.get_param_data(inport, outport, [0, 18, macro_id, 1], 'int', device_id)['value']
   return {
       'effect_id': effect_id,
       'param_id': param_id,
   }
   # NB: to get effect name, get label of [0, <effect_id>]
   # NB: to get the param name/value, get [0, <effect_id>, <algo_id>, <param_id>], where algo ids gotten w/ get_program_info

def get_current_program_macros(inport, outport, device_id = 0x7f):
    out = []
    for i in range(0, 10):
        v = get_current_program_macro(inport, outport, i, device_id)
        if v['param_id'] == 255: # unassigned
            break
        out.append(v)
    return out

def get_current_program_context(inport, outport, device_id = 0x7f, control_tree=None):
    curr_p_id = mpx1_sysex.get_current_program(inport, outport, device_id)['value']
    curr_p_info = mpx1_sysex.get_program_info(inport, outport, curr_p_id, device_id)
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
            effect_label = mpx1_sysex.get_param_label(inport, outport, effect_cl, device_id)['label'].strip()
            param_type = mpx1_sysex.get_param_type(inport, outport, param_cl, device_id)
            param_desc = mpx1_sysex.get_param_desc(inport, outport, param_type, device_id)

        param_data = mpx1_sysex.get_param_data(inport, outport, param_cl, device_id=device_id)
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
