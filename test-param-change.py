#!/usr/bin/env python3

import os
import signal
import time

from pprint import pprint
from icecream import ic

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import mido

import lib.mpx1.debug_state as debug_state
import lib.mpx1.sysex as mpx1_sysex
import lib.mpx1.param as mpx1_program_params



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
    # pgm = 120
    # mpx1_sysex.set_current_program(outport, pgm, DEVICE_ID)
    # # mpx1_sysex.set_current_program_safe(inport, outport, pgm, DEVICE_ID)
    # resp = mpx1_sysex.get_current_program(inport, outport, DEVICE_ID)
    # current_program = resp['value']
    # print("Current program is #" + str(current_program + 1))

    # p_macros = mpx1_program_params.get_current_program_macros(inport, outport, DEVICE_ID)
    # pprint(p_macros)

    pgm_ctx = mpx1_program_params.get_current_program_context(inport, outport, DEVICE_ID)
    pprint(pgm_ctx)

except KeyboardInterrupt as e:
    cleanup_mido()



## CLEANUP

cleanup_mido()
