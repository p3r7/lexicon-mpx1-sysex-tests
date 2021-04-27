
from pprint import pprint

import lib.mpx1.sysex as mpx1_sysex


## GLOBAL PARAMS

def update_master_mix(outport, v, device_id = 0x7f):
    mpx1_sysex.set_param_data(outport, [0, 19, 12], 1, v, 'int', device_id)

def update_master_level(outport, v, device_id = 0x7f):
    mpx1_sysex.set_param_data(outport, [0, 19, 13], 1, v, 'int', device_id)



## CURRENT PROGRAM MACRO PARAMS (SOFT ROW)
