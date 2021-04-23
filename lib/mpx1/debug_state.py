


## STATE

DEBUG = False
DEBUG_MIDI = False



## ACCESSORS

def is_enabled():
    return DEBUG

def is_enabled_midi():
    return DEBUG_MIDI

def enable():
    global DEBUG
    DEBUG = True

def enable_midi():
    global DEBUG_MIDI
    DEBUG_MIDI = True
