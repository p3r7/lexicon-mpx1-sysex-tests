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

from pythonosc.osc_server import AsyncIOOSCUDPServer, BlockingOSCUDPServer
from pythonosc.dispatcher import Dispatcher

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

OSC_SRV_HOST = "0.0.0.0"
OSC_SRV_PORT = 5005

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



## STATE - LOCKS

IS_CHANGING_PGM = False



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



## FNS - SYSEX

def register_update_macro(macro_id, v):
    global midi_param_send_qs
    if macro_id <= len(pgm_ctx['soft_params']):
        macro = pgm_ctx['soft_params'][macro_id]
        v_min = decode_negative_maybe(macro['desc']['vals'][0]['min'])
        v_max = decode_negative_maybe(macro['desc']['vals'][0]['max'])
        new_v = lininterpol_cc(v, v_min, v_max)
        cl = tuple(macro['cl'])

        # print("Setting "+macro['desc']['label']+" to "+str(new_v))
        pgm_ctx['soft_params'][macro_id]['value'] = new_v
        midi_param_send_qs[cl] = {
            'size': macro['desc']['param_size'],
            'value': new_v,
            'type': 'int', # NB: can this differ?
        }



## COROUTINE - MIDO LISTEN CC

def cc_id_to_macro_id(cc_id):
    return cc_id - 1

def process_cc_msg_maybe(msg):
    if msg.type == 'control_change':
        rcv = msg.bytes()
        cc_id = rcv[1]
        macro_id = cc_id_to_macro_id(cc_id)
        v = rcv[2]
        register_update_macro(macro_id, v)


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



## COROUTINE - MIDO LISTEN LEXICON ANSWERS

def process_lexicon_msg_maybe(msg):
    global pgm_ctx
    print("----------")
    msg_b = msg.bytes()
    pprint(msg)
    # pprint(msg_b)
    if mpx1_sysex.is_change_program_msg(msg_b, 'int', DEVICE_ID):
        print("recognized PGM CHANGE")
        IS_CHANGING_PGM = True
        pgm_ctx = mpx1_sysex.get_current_program_context(inport, outport, DEVICE_ID, control_tree)
        IS_CHANGING_PGM = False
        pprint(pgm_ctx)
    elif mpx1_sysex.is_param_data_resp(msg_b, DEVICE_ID):
        cl = mpx1_sysex.get_param_data_resp_cl(msg_b)
        is_macro_param = False
        for i, macro in enumerate(pgm_ctx['soft_params']):
            if cl == macro['cl']:
                is_macro_param = True
                v = mpx1_sysex.get_param_data_resp_v(msg_b, 'int')
                pgm_ctx['soft_params'][i]['value'] = v
                print("recognized update of soft param #" + str(i) + " (" + macro['label'].strip() + ") value to " + str(v))
                break
        if not is_macro_param:
            print("update of unknown param")
    else:
        print("unrecognized message")

async def process_input_lexicon():
    while True:
        for msg in inport.iter_pending():
            if not IS_CHANGING_PGM:
                process_lexicon_msg_maybe(msg)
        await asyncio.sleep(1/1000)



## COROUTINE - CLOCKED SYSEX SEND

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



## INIT - OSC SERVER ROUTES

def osc_macro_handler(address, *args):
    macro_id = address.replace("/param/macro/", "", 1)
    macro_id = int(macro_id)
    v = args[0]
    register_update_macro(macro_id, v)

def osc_pgm_change_handler(address, *args):
    global IS_CHANGING_PGM
    pgm_id = args[0] - 1
    IS_CHANGING_PGM = True
    mpx1_sysex.set_current_program(outport, pgm_id, DEVICE_ID)

osc_dispatcher = Dispatcher()
osc_dispatcher.map("/param/macro/*", osc_macro_handler)
osc_dispatcher.map("/program", osc_pgm_change_handler)



## COROUTINE - OSC SERVER

async def osc_listen():
    while True:
        await asyncio.sleep(1/1000)

async def osc_listen_server():
    server = AsyncIOOSCUDPServer((OSC_SRV_HOST, OSC_SRV_PORT), osc_dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving
    await osc_listen()  # Enter main loop of program
    transport.close()  # Clean up serve endpoint



## MAIN

control_tree = None
with open("control_tree_flat.pickle", "rb") as f:
    control_tree = pickle.load(f)

loop = asyncio.get_event_loop()
midi_param_send_clock = loop.create_task(midi_param_send())
process_input_cc_task = loop.create_task(process_input_cc())
process_input_lexicon_task = loop.create_task(process_input_lexicon())
process_osc_listen_server = loop.create_task(osc_listen_server())


try:

    # empty any message in midi buffer
    # NB: this isn't working as expected, we might need a blocking loop in an asyncio task that we'd make run for 100ms then kill
    i = 0
    while i < 10:
        for msg in inport.iter_pending():
            pass
        i += 1

    IS_CHANGING_PGM = True
    pgm_ctx = mpx1_sysex.get_current_program_context(inport, outport, DEVICE_ID, control_tree)
    IS_CHANGING_PGM = False
    pprint(pgm_ctx)

    loop.run_forever()
except KeyboardInterrupt as e:
    cleanup_mido()
except asyncio.CancelledError as e:
    cleanup_mido()



## CLEANUP

cleanup_mido()
