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
    mpx1_sysex.set_display(outport, "hello", DEVICE_ID)
    # mpx1_sysex.set_display_all_special_chars(outport, DEVICE_ID)

    display_dump = mpx1_sysex.display_dump(inport, outport, DEVICE_ID)
    pprint(display_dump)

    # special_chars = mpx1_sysex.dump_custom_characters(inport, outport, DEVICE_ID)
    # pprint(special_chars)
except KeyboardInterrupt as e:
    cleanup_mido()



## CLEANUP

cleanup_mido()
