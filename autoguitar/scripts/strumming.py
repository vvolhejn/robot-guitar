import logging
import time

import mido
import numpy as np

from autoguitar.control.strummer import Strummer
from autoguitar.dsp.input_stream import InputStream
from autoguitar.midi_utils import find_midi_input
from autoguitar.motor import MotorController, get_motor

logging.basicConfig(level=logging.INFO)


def main():
    motor = get_motor(motor_number=1)

    # Do this early in case there's an error
    try:
        midi_input_name = find_midi_input()
        print("Using MIDI input:", midi_input_name)
        inport = mido.open_input(midi_input_name)
    except OSError as e:
        logging.error(e)
        logging.info("MIDI control will not be run.")
        inport = None

    with (
        MotorController(motor=motor, max_steps=int(1e9)) as mc,
        InputStream(block_size=512) as input_stream,
    ):
        # Randomize the motor position for testing purposes
        mc.move(np.random.randint(-mc.steps_per_turn(), mc.steps_per_turn()))

        strummer = Strummer(input_stream=input_stream, motor_controller=mc)

        strummer.calibrate()
        print("Calibration done")

        # Play a strumming pattern
        time.sleep(1)
        sleep = 0.1
        for _ in range(4):
            strummer.strum()
            time.sleep(sleep)
            strummer.mute()
            time.sleep(sleep * 2)

        if inport is None:
            print("MIDI control not available, exiting.")
            return

        for msg in inport:
            print(msg)
            if msg.type == "note_on":
                strummer.strum()
            elif msg.type == "note_off":
                strummer.mute()


if __name__ == "__main__":
    main()
