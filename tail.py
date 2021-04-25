
import os
import signal

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import mido



## INIT - MIDI

mido.set_backend('mido.backends.pygame')

inport = mido.open_input('MidiSport 1x1 MIDI 1')

def cleanup_mido():
    inport.close()

def handler(signum, frame):
    cleanup_mido()

signal.signal(signal.SIGHUP, handler)



## MAIN

try:
    for msg in inport:
        print("-----------------")
        print(msg)
        print(msg.hex())
except KeyboardInterrupt as e:
    cleanup_mido()
