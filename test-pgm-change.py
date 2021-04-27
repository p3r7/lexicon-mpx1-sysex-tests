#!/usr/bin/env python3

import os
import signal

from pprint import pprint
from icecream import ic

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import mido

import lib.mpx1.debug_state as debug_state
import lib.mpx1.sysex as mpx1_sysex



## CONF

MIDO_BACKEND = 'mido.backends.pygame'

INPORT_LABEL = 'MidiSport 1x1 MIDI 1'
OUTPORT_LABEL = 'MidiSport 1x1 MIDI 1'

DEVICE_ID = 0x00



## INIT - MIDI

mido.set_backend('mido.backends.pygame')

inport = mido.open_input(INPORT_LABEL)
outport = mido.open_output(OUTPORT_LABEL)

def cleanup_mido():
    inport.close()
    outport.close()

def handler(signum, frame):
    cleanup_mido()

signal.signal(signal.SIGHUP, handler)



## INIT - DEBUG

DEBUG = True
DEBUG_MIDI = True

if DEBUG:
    debug_state.enable()

if DEBUG_MIDI:
    debug_state.enable_midi()
    ic.enable()
else:
    ic.disable()
    ic.configureOutput(includeContext=True)



## FNS - MIDI PGM CHANGE

def msg_change_program_std(pgm_id):
    return mido.Message('program_change', program=pgm_id-1)

def change_pgm_std(outport, pgm_id, device_id):
    snd = msg_change_program_std(pgm_id)
    outport.send(snd)



## MAIN

mpx_program=200

try:

    # change_pgm_std(outport, mpx_program, DEVICE_ID)
    mpx1_sysex.set_current_program(outport, mpx_program, DEVICE_ID)

    resp = mpx1_sysex.get_current_program(inport, outport, DEVICE_ID)
    current_program = resp['value']
    print("Current program is #" + str(current_program + 1))

except KeyboardInterrupt as e:
    cleanup_mido()



## CLEANUP

cleanup_mido()
