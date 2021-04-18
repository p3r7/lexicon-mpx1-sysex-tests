import mido
# import mido.backends.pygame
from pprint import pprint



## MIDO INIT

mido.set_backend('mido.backends.pygame')

# pprint(mido.get_output_names())
# pprint(mido.get_input_names())

outport = mido.open_output('MidiSport 1x1 MIDI 1')



## HELPER FNS

def nibblize(v):
    v_str = hex(v)[2:]
    if len(v_str) == 1:
        return [int(v_str[0], 16), 0]
    else:
        return [int(v_str[1], 16), int(v_str[0], 16)]

def msg_change_program_std(pgm_id):
    return mido.Message('program_change', program=pgm_id-1)

def msg_change_program_sysex(pgm_id):
    v = pgm_id-1
    v_nibble = nibblize(v)
    payload = [0x06, 0x09, 0x00, 0x01, 0x02, 0x00, 0x00, 0x00, v_nibble[0], v_nibble[1], 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x01, 0x00, 0x00, 0x09, 0x00, 0x00, 0x00]
    return mido.Message('sysex', data=payload)



## MAIN

mpx_program=200

msg = msg_change_program_sysex(mpx_program)

print(msg.hex())

outport.send(msg)



## CLEAN EXIT

# outport.reset()
outport.close()
