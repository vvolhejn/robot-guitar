import random
import time

import mido
from mido import Message

# Open a virtual MIDI port to send messages.
outport = mido.open_output("my_virtual_port", virtual=True)
inport = mido.open_input("my_virtual_port", virtual=True)

# minor blues scale
scale = [60, 62, 63, 65, 66, 67, 72]

try:
    print("Sending MIDI notes.")
    while True:
        # Send a note on and note off message.
        note = random.choice(scale)
        outport.send(Message("note_on", note=note, velocity=64))
        time.sleep(0.3 * random.randint(1, 4))
        outport.send(Message("note_off", note=note, velocity=64))
        time.sleep(0.01)
except Exception as e:
    print(e)
finally:
    # Close the port when done
    outport.close()
