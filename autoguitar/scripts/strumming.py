import logging
import time

import numpy as np

from autoguitar.control.strummer import Strummer
from autoguitar.dsp.input_stream import InputStream
from autoguitar.motor import MotorController, get_motor

logging.basicConfig(level=logging.INFO)


def main():
    steps_per_turn = 1600

    motor = get_motor(motor_number=1)

    with MotorController(motor=motor, max_steps=int(1e9)) as mc:
        # Randomize the motor position for testing purposes
        mc.move(np.random.randint(-steps_per_turn, steps_per_turn))

        with InputStream() as input_stream:
            strummer = Strummer(input_stream=input_stream, motor_controller=mc)

            strummer.calibrate()
            print("Calibration done")

            # Play a strumming pattern
            time.sleep(1)
            sleep = 0.1
            for _ in range(20):
                strummer.strum()
                time.sleep(sleep)
                strummer.mute()
                time.sleep(sleep * 2)


if __name__ == "__main__":
    main()
