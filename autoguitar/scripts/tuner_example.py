import time

import numpy as np

from autoguitar.motor import MotorController, get_motor
from autoguitar.pitch_detector import PitchDetector, Timestamp

n_steps = 0
desired_freq = 70
max_reading_age = 0.1


def tuner():
    n_steps = 1
    desired_freq = 70
    max_reading_age = 0.1

    motor = get_motor()

    with MotorController(motor=motor, max_steps=10000) as mc:

        def foo(data: tuple[float, Timestamp]):
            nonlocal desired_freq
            print(data)

            frequency, timestamp = data

            reading_age = time.time() - timestamp
            if reading_age > max_reading_age:
                frequency = np.nan

            if np.isnan(frequency):
                return

            if mc.is_moving():
                print("Still moving, skipping...")
                return

            if frequency > desired_freq + 1:
                # print("Wind less!")
                mc.move(-n_steps)
            elif frequency < desired_freq - 1:
                # print("Wind more!")
                mc.move(n_steps)
            else:
                print("In tune!")
                if desired_freq == 70:
                    desired_freq = 140
                else:
                    desired_freq = 70

    with PitchDetector() as pitch_detector:
        pitch_detector.on_reading.subscribe(foo)
        with MotorController(motor=motor, max_steps=10000) as mc:
            print("Starting (pitch detector takes a few seconds to start up)")
            while True:
                time.sleep(1)  # just to keep the thread alive.


if __name__ == "__main__":
    tuner()
