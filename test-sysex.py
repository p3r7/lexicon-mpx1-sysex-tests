import mido
# import mido.backends.pygame
from pprint import pprint

mido.set_backend('mido.backends.pygame')


inport = mido.open_input('MidiSport 1x1 MIDI 1')
outport = mido.open_output('MidiSport 1x1 MIDI 1')


# https://mido.readthedocs.io/en/latest/messages.html#system-exclusive-messages



# device inquiry message
# NB: 7F means all devices
# device_inquiry='F0 06 09 7F 06 01 F7'

# device_inquiry_msg = []
# for b in device_inquiry.split(' '):
#     for b2 in b:
#         print(b2)
#         device_inquiry_msg += bytes.fromhex(b2)

# pprint(device_inquiry_msg)

# msg = mido.Message('sysex', data=device_inquiry_msg)



# NB: 7F means all devices
# device_inquiry_payload = [0x06, 0x09, 0x7f, 0x06, 0x01]
device_inquiry_payload = [6,9,0,1,2,0,0,0,2,0,0,0,3,0,0,0,0,0,0,0,3,1,0,0,9,0,0,0]

msg = mido.Message('sysex', data=device_inquiry_payload)

print(msg.hex())

# outport.send(msg)
# rcv_msg = inport.receive()

for msg in inport:
    print("Human: ", msg)
    print("Hex: ", msg.hex())


inport.close()
# outport.reset()
outport.close()
