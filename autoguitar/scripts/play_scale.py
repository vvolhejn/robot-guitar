import logging
import time

import librosa
import numpy as np

from autoguitar.control.strummer import Strummer
from autoguitar.dsp.input_stream import InputStream
from autoguitar.motor import MotorController, get_motor
from autoguitar.tuner import Tuner
from autoguitar.tuner_strategy import ModelBasedTunerStrategy

logging.basicConfig(level=logging.INFO)


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
            initial_target_frequency=float(librosa.note_to_hz("C3")),
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
            [(mc0.cur_steps, frequency)], coef=13.7
        )
        print(tuner_strategy)

        # Stop the tuner from moving the string, we'll be doing that manually now
        # using the tuner_strategy.
        tuner.unsubscribe()

        # Repeatedly play a few notes and then re-calibrate the strategy.
        for _ in range(10):
            strumming_measurements = []
            # notes = ["B2", "C#3", "D#3", "E3", "F#3", "G#3", "A#3", "B3"]
            # notes = ["B2", "D#3", "F#3", "A#3", "B3", "G#3", "E3", "C#3"]
            notes = ["F#3", "G#3", "A#3", "C4", "B3", "A3", "G3", "F3"]
            for note in notes:
                target_frequency = float(librosa.note_to_hz(note))

                # Hack: the frequency we reach depends on whether we're going from
                # above or below because the string has a bit of slack. We correct
                # for that heuristically
                movement_correction_cents = 100
                movement_correction = 2 ** (movement_correction_cents / 1200)

                steps_naive = tuner_strategy.get_target_steps(target_frequency)

                if steps_naive > mc0.cur_steps:
                    # going up, move a bit more
                    target_frequency *= movement_correction
                else:
                    # going down, move a bit less
                    target_frequency /= movement_correction

                steps = tuner_strategy.get_target_steps(target_frequency)
                print(
                    f"Corrected from {librosa.note_to_hz(note):.2f} to {target_frequency:.2f} "
                    f"and {steps_naive} to {steps} steps."
                )

                mc0.set_target_steps(steps, wait=True)
                strummer.strum()
                time.sleep(0.5)
                tuner.pitch_detector.frequency_readings.clear()
                time.sleep(0.5)
                frequencies = [f for f, _ in tuner.pitch_detector.frequency_readings]
                frequency = float(np.nanmean(frequencies))

                offset_cents = (
                    get_cents_between_frequencies(target_frequency, frequency)
                    if not np.isnan(frequency)
                    else np.nan
                )

                print((note, steps, target_frequency, frequency, offset_cents))
                print()
                if not np.isnan(frequency):
                    strumming_measurements.append((steps, frequency))

            print(strumming_measurements)
            tuner_strategy = ModelBasedTunerStrategy.from_readings(
                strumming_measurements
            )
            print(tuner_strategy)


if __name__ == "__main__":
    main()
