import time

import readchar

from autoguitar.motor import MotorController, get_motor
from autoguitar.pitch_detector import PitchDetector


def manual_control():
    print("Press arrow keys or q to exit")

    n_steps = 25

    motor = get_motor()
    with PitchDetector() as pitch_detector:
        with MotorController(motor=motor, max_steps=10000) as mc:
            while True:
                print(
                    f"#steps={mc.cur_steps} "
                    f"freq={pitch_detector.get_frequency()[0]:.2f} Hz"
                )

                key = readchar.readkey()

                if mc.is_moving():
                    print("Still moving, skipping...")
                    continue

                if key.lower() == "d":
                    print("You pressed Wind less!")
                    mc.move(-n_steps)
                    time.sleep(0.1)
                elif key.lower() == "f":
                    print("You pressed Wind more!")
                    mc.move(n_steps)
                    time.sleep(0.1)
                elif key == "q":
                    print("Exiting...")
                    break


if __name__ == "__main__":
    manual_control()
