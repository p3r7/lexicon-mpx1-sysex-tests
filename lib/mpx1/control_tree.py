
from pprint import pprint

import lib.mpx1.debug_state as debug_state
import lib.mpx1.sysex as mpx1_sysex



## BUILD CONTROL TREE

# p5
def make(inport, outport, device_id = 0x7f, control_level=[], max_cl_depth=5):

    if debug_state.is_enabled:
        print("------------------------")
        pprint(control_level)

    p_type = mpx1_sysex.get_param_type(inport, outport, control_level, device_id)
    p_desc = mpx1_sysex.get_param_desc(inport, outport, p_type, device_id)
    p = {
        'type': p_type,
        'desc': p_desc,
    }

    if debug_state.is_enabled:
        print(hex(p_type) + " (" + str(p_type) + ") - " + p_desc['label'])

    # non-editable param, i.e. tree branching
    if p_desc['control_flags'] & 0x04 != 0 \
       and len(control_level)+1 <= max_cl_depth \
       and not (p_desc['label'] in ['CC        ', 'Cont Remap ', 'Ctl Smooth', 'Map        ', 'ProgramDump']):
        if debug_state.is_enabled:
            print('BRANCH!')
        p['children'] = {}
        for v in p_desc['vals']:
            for cl_id in range(v['min'], v['max']+1):
                cl = control_level.copy()
                cl.append(cl_id)
                branch = make(inport, outport, device_id, cl)
                p['children'][cl_id] = branch
    return p



## BUILD PARAMS LIST

## NB: this is redundant w/ `make`
def make_desc_list(inport, outport, device_id):
    sysconf = get_system_config(inport, outport, device_id)
    nb_params = sysconf['nb_params']

    p_type_desc_map={}
    for p_type in range(0, nb_params):
        p_desc = get_param_desc(inport, outport, p_type, device_id)
        p_type_desc_map[p_type] = p_desc

    return p_type_desc_map
