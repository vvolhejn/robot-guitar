import time

import click
import readchar

from autoguitar.motor import MotorController, get_motor
from autoguitar.pitch_detector import PitchDetector


def manual_control(pitch_detector: PitchDetector | None):
    n_steps = 200

    motors = [get_motor(motor_number=0), get_motor(motor_number=1)]
    with (
        MotorController(motor=motors[0], max_steps=10000) as mc0,
        MotorController(motor=motors[1], max_steps=10000) as mc1,
    ):
        while True:
            if pitch_detector is not None:
                print(
                    f"#steps={mc0.cur_steps} "
                    f"freq={pitch_detector.get_frequency()[0]:.2f} Hz"
                )
            else:
                print(f"#steps={mc0.cur_steps}")

            key = readchar.readkey()

            if key.lower() == "q":
                print("Exiting...")
                break

            controls = [(0, mc0, "d", "f"), (1, mc1, "c", "v")]

            for i, mc, key_less, key_more in controls:
                if mc.is_moving():
                    print(f"Motor {i}: still moving, skipping...")
                    continue

                if key.lower() == key_less:
                    print(f"Motor {i}: Wind less!")
                    mc.move(-n_steps)
                    time.sleep(0.1)
                elif key.lower() == key_more:
                    print(f"Motor {i}: Wind more!")
                    mc.move(n_steps)
                    time.sleep(0.1)


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
