import logging
import time

import librosa
import numpy as np

from autoguitar.control.strummer import Strummer
from autoguitar.dsp.input_stream import InputStream
from autoguitar.motor import MotorController, get_motor
from autoguitar.tuning.tuner import Tuner
from autoguitar.tuning.tuner_strategy import ModelBasedTunerStrategy

logging.basicConfig(level=logging.INFO)


SLACK_CORRECTION_CENTS = 15
INITIAL_NOTE = "A2"
# NOTES = ["B1", "C#1", "D#2", "E2", "F#2", "G#2", "A#2", "B2"]
# NOTES = ["B1", "D#2", "F#2", "A#2", "B2", "G#2", "E2", "C#2"]
# NOTES = ["F#2", "G#2", "A#2", "C3", "B2", "A2", "G2", "F2"]
NOTES = ["A#2", "C3", "B2", "A2", "G2", "F2", "F#2", "G#2"]
N_REPETITIONS = 5


def get_cents_between_frequencies(f1: float, f2: float) -> int:
    return int(1200 * np.log2(f2 / f1))


def main():
    motors = [
        get_motor(motor_number=0),
        get_motor(motor_number=1),
    ]

    with (
        InputStream(block_size=512) as input_stream,
        MotorController(motor=motors[0], max_steps=10000) as mc0,
        MotorController(motor=motors[1], max_steps=10000) as mc1,
    ):
        # Randomize the motor position for testing purposes
        mc1.move(
            np.random.randint(-mc1.steps_per_turn(), mc1.steps_per_turn()), wait=True
        )

        strummer = Strummer(input_stream=input_stream, motor_controller=mc1)
        strummer.calibrate()

        # Create the tuner only after the strummer has been calibrated
        # so that it doesn't move the string while we're calibrating
        tuner = Tuner(
            input_stream=input_stream,
            motor_controller=mc0,
            initial_target_frequency=float(librosa.note_to_hz(INITIAL_NOTE)),
        )

        # Allow some time for the tuner to move to the target note
        for i in range(5):
            strummer.strum()
            time.sleep(1)

        # Initialize the tuner strategy with a single reading, using a fixed coefficient
        tuner.pitch_detector.frequency_readings.clear()
        strummer.strum()
        time.sleep(2)
        frequencies = [f for f, _ in tuner.pitch_detector.frequency_readings]
        frequency = float(np.nanmean(frequencies))
        tuner_strategy = ModelBasedTunerStrategy.from_readings(
            [(mc0.cur_steps, frequency)],
            coef=4.35,
            slack_correction_cents=SLACK_CORRECTION_CENTS,
        )
        print(tuner_strategy)

        # Stop the tuner from moving the string, we'll be doing that manually now
        # using the tuner_strategy.
        tuner.unsubscribe()

        # Repeatedly play a few notes and then re-calibrate the strategy.
        for _ in range(N_REPETITIONS):
            strumming_measurements = []

            print(
                "".join(
                    f"{x:>14}"
                    for x in [
                        "Note",
                        "Steps naive",
                        "Steps",
                        "Frequency",
                        "Cents offset",
                    ]
                )
            )

            for note in NOTES:
                target_frequency_naive = float(librosa.note_to_hz(note))

                steps_naive = tuner_strategy.get_target_steps_raw(
                    target_frequency_naive, with_slack_correction=False
                )
                steps = tuner_strategy.get_target_steps_raw(
                    target_frequency_naive, with_slack_correction=True
                )

                mc0.set_target_steps(steps, wait=True)
                strummer.strum()
                time.sleep(0.5)
                tuner.pitch_detector.frequency_readings.clear()
                time.sleep(0.5)
                frequencies = [f for f, _ in tuner.pitch_detector.frequency_readings]
                frequency = float(np.nanmean(frequencies))

                offset_cents = (
                    get_cents_between_frequencies(target_frequency_naive, frequency)
                    if not np.isnan(frequency)
                    else np.nan
                )

                print(
                    "".join(
                        f"{x:>14}"
                        for x in [
                            note,
                            steps_naive,
                            steps,
                            f"{frequency:.2f}",
                            offset_cents,
                        ]
                    )
                )

                if not np.isnan(frequency):
                    strumming_measurements.append((steps, frequency))

            tuner_strategy = ModelBasedTunerStrategy.from_readings(
                strumming_measurements
            )
            print("New strategy:", tuner_strategy)


if __name__ == "__main__":
    main()
