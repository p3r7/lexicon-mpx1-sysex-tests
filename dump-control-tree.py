#!/usr/bin/env python3

import signal

from pprint import pprint
from icecream import ic

import mido


import lib.mpx1.debug_state as debug_state
import lib.mpx1.sysex as mpx1_sysex
import lib.mpx1.control_tree as mpx1_control_tree



## CONF

MIDO_BACKEND = 'mido.backends.pygame'

INPORT_LABEL = 'MidiSport 1x1 MIDI 1'
OUTPORT_LABEL = 'MidiSport 1x1 MIDI 1'

DEVICE_ID = 0x00



## INIT - MIDI

mido.set_backend(MIDO_BACKEND)

inport = mido.open_input(INPORT_LABEL)
outport = mido.open_output(OUTPORT_LABEL)

# outport.reset()

def cleanup_mido():
    inport.close()
    outport.close()

def handler(signum, frame):
    cleanup_mido()

signal.signal(signal.SIGHUP, handler)



## INIT - DEBUG

DEBUG = True
DEBUG_MIDI = False

if DEBUG:
    debug_state.enable()

if DEBUG_MIDI:
    debug_state.enable_midi()
    ic.enable()
else:
    ic.disable()
    ic.configureOutput(includeContext=True)



## MAIN

try:

    # NB: this is slow AF
    control_tree = mpx1_control_tree.make(inport, outport, DEVICE_ID)

    # pprint(control_tree['desc']['label'])
    # pprint(control_tree['children'][0]['desc']['label'])
    # pprint(control_tree['children'][0]['children'][2]['desc']['label'])
    # pprint(control_tree['children'][0]['children'][2]['children'][1]['desc']['label'])
    # pprint(control_tree['children'][0]['children'][2]['children'][1]['children'][2]['desc']['label'])

except KeyboardInterrupt as e:
    cleanup_mido()



## CLEANUP

cleanup_mido()
