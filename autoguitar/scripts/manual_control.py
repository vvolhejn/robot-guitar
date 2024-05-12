import time

import click
import readchar

from autoguitar.motor import MotorController, get_motor
from autoguitar.pitch_detector import PitchDetector


def manual_control(pitch_detector: PitchDetector | None):
    n_steps = 25

    motor = get_motor()
    with MotorController(motor=motor, max_steps=10000) as mc:
        while True:
            if pitch_detector is not None:
                print(
                    f"#steps={mc.cur_steps} "
                    f"freq={pitch_detector.get_frequency()[0]:.2f} Hz"
                )
            else:
                print(f"#steps={mc.cur_steps}")

            key = readchar.readkey()

            if mc.is_moving():
                print("Still moving, skipping...")
                continue

            if key.lower() == "d":
                print("Wind less!")
                mc.move(-n_steps)
                time.sleep(0.1)
            elif key.lower() == "f":
                print("Wind more!")
                mc.move(n_steps)
                time.sleep(0.1)
            elif key == "q":
                print("Exiting...")
                break


@click.command()
@click.option("--pitch-detection/--no-pitch-detection", default=True)
def manual_control_cli(pitch_detection: bool = True):
    print("d: wind less, f: wind more, q: exit")

    if pitch_detection:
        # Only instantiate if needed. If the audio interface is not available,
        # we get an error here.
        with PitchDetector() as pitch_detector:
            manual_control(pitch_detector)
    else:
        manual_control(None)


if __name__ == "__main__":
    manual_control_cli()
