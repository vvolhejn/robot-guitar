import time

import click
import librosa
import numpy as np
import readchar

from autoguitar.dsp.input_stream import InputStream
from autoguitar.dsp.pitch_detector import PitchDetector
from autoguitar.motor import MotorController, get_motor


def manual_control(pitch_detector: PitchDetector | None):
    n_steps = [100, 25]

    motors = [
        get_motor(motor_number=0),
        get_motor(motor_number=1),
    ]
    with (
        MotorController(motor=motors[0], max_steps=n_steps[0] * 100) as mc0,
        MotorController(motor=motors[1], max_steps=n_steps[1] * 100) as mc1,
    ):
        while True:
            if pitch_detector is not None:
                freq = pitch_detector.get_frequency()[0]
                note = librosa.hz_to_note(freq) if not np.isnan(freq) else None
                print(f"#steps={mc0.cur_steps}, freq={freq:.2f} Hz, note={note}")
            else:
                print(f"#steps={mc0.cur_steps}")

            key = readchar.readkey()

            if key.lower() == "q":
                print("Exiting...")
                break

            controls = [(0, mc0, "d", "f", n_steps[0]), (1, mc1, "c", "v", n_steps[1])]

            for i, mc, key_less, key_more, ns in controls:
                if mc.is_moving():
                    print(f"Motor {i}: still moving, skipping...")
                    continue

                if key.lower() == key_less:
                    print(f"Motor {i}: Wind less!")
                    mc.move(-ns)
                    time.sleep(0.1)
                elif key.lower() == key_more:
                    print(f"Motor {i}: Wind more!")
                    mc.move(ns)
                    time.sleep(0.1)


@click.command()
@click.option("--pitch-detection/--no-pitch-detection", default=True)
def manual_control_cli(pitch_detection: bool = True):
    print("d/f: control pitch motor, c/v: control pluck motor, q: exit")

    if pitch_detection:
        # Only instantiate if needed. If the audio interface is not available,
        # we get an error here.
        with InputStream(block_size=512) as input_stream:
            pitch_detector = PitchDetector(input_stream=input_stream)
            manual_control(pitch_detector)
    else:
        manual_control(None)


if __name__ == "__main__":
    manual_control_cli()
