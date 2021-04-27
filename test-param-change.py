#!/usr/bin/env python3

import os
import signal
import math
import asyncio
import _pickle as pickle

from pprint import pprint
from icecream import ic

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import mido

import lib.mpx1.debug_state as debug_state
import lib.mpx1.sysex as mpx1_sysex
from lib.core.binencoding import decode_negative_maybe



## CONF

MIDO_BACKEND = 'mido.backends.pygame'

MIDI_SEND_PARAM_RATE = 1/10
# MIDI_SEND_PARAM_RATE = 1

CC_INPORT_LABEL = 'LPD8 MIDI 1'
INPORT_LABEL = 'MidiSport 1x1 MIDI 1'
OUTPORT_LABEL = 'MidiSport 1x1 MIDI 1'

DEVICE_ID = 0x00



## INIT - MIDI

mido.set_backend(MIDO_BACKEND)

cc_inport = mido.open_input(CC_INPORT_LABEL)
inport = mido.open_input(INPORT_LABEL)
outport = mido.open_output(OUTPORT_LABEL)

# outport.reset()

def cleanup_mido():
    cc_inport.close()
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



## FNS - CORE

def lininterpol_cc(v_in, v_min_out, v_max_out, v_min_in=0, v_max_in=127):
    if v_min_in > 0:
       v_min_in = 0
       v_max_in -= v_min_in

    og_v_min_out = v_min_out
    if v_min_out > 0:
       v_min_out = 0
       v_max_out -= og_v_min_out
    elif v_min_out < 0:
       v_min_out = 0
       v_max_out -= og_v_min_out
    return round(v_max_out * v_in/v_max_in) + og_v_min_out



## FNS - CORE - COROUTINES

def make_stream():
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()
    def callback(message):
        loop.call_soon_threadsafe(queue.put_nowait, message)
    async def stream():
        while True:
            yield await queue.get()
    return callback, stream()



## COROUTINES - MIDO LISTEN

def process_cc_msg_maybe(msg):
    if msg.type == 'control_change':
        rcv = msg.bytes()
        cc_id = rcv[1]
        macro_id = cc_id - 1
        v = rcv[2]

        if macro_id <= len(pgm_ctx['soft_params']):
            macro = pgm_ctx['soft_params'][macro_id]
            v_min = decode_negative_maybe(macro['desc']['vals'][0]['min'])
            v_max = decode_negative_maybe(macro['desc']['vals'][0]['max'])
            new_v = lininterpol_cc(v, v_min, v_max)
            # print("Setting "+macro['desc']['label']+" to "+str(new_v))
            cl = tuple(macro['cl'])
            midi_param_send_qs[cl] = {
                'size': macro['desc']['param_size'],
                'value': new_v,
                'type': 'int', # NB: can this differ?
            }

# Alt version w/ an asynio stream
# does not work w/ pygame backend, and could use a thread anyway

# async_mido_cb, async_mido_stream = make_stream()
# cc_inport = mido.open_input(CC_INPORT_LABEL, callback=async_mido_cb)
# async def process_input_cc():
#     async for msg in async_mido_stream:
#         process_cc_msg_maybe(msg)

async def process_input_cc():
    while True:
        for msg in cc_inport.iter_pending():
            process_cc_msg_maybe(msg)
        await asyncio.sleep(1/1000)



## COROUTINES - CLOCKED SEND

midi_param_send_qs={}
midi_param_prev_qs={}

async def midi_param_send():
    while True:
        # print('trigger')

        for cl, v_props in midi_param_send_qs.items():
            if cl in midi_param_prev_qs and midi_param_prev_qs[cl] == v_props['value']:
                continue
            midi_param_prev_qs[cl] = v_props['value']
            mpx1_sysex.set_param_data(outport, cl, v_props['size'], v_props['value'], v_props['type'], DEVICE_ID)
        await asyncio.sleep(MIDI_SEND_PARAM_RATE)




## MAIN

loop = asyncio.get_event_loop()
midi_param_send_clock = loop.create_task(midi_param_send())
process_input_cc_task = loop.create_task(process_input_cc())

control_tree = None
with open("control_tree_flat.pickle", "rb") as f:
    control_tree = pickle.load(f)

try:
    pgm_ctx = mpx1_sysex.get_current_program_context(inport, outport, DEVICE_ID, control_tree)
    pprint(pgm_ctx)

    loop.run_forever()
    # loop.run_until_complete(process_input_cc_task)
    # loop.run_until_complete(midi_param_send_clock)


except KeyboardInterrupt as e:
    cleanup_mido()
    # process_input_cc_task.cancel()
    # midi_param_send_clock.cancel()
except asyncio.CancelledError as e:
    cleanup_mido()



## CLEANUP

cleanup_mido()
midi_param_send_clock.cancel()
