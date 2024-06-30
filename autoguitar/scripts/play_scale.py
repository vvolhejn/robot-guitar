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
            initial_target_frequency=float(librosa.note_to_hz("A2")),
        )

        # Allow some time for the tuner to move to the target note
        for i in range(5):
            strummer.strum()
            time.sleep(1)

        tuner.unsubscribe()

        def go_to_frequency_and_measure(
            target_frequency: float, steps_per_move: int
        ) -> list[tuple[int, float]]:
            positions_and_frequencies = []

            while True:
                mc0.move(steps_per_move, wait=True)
                strummer.strum()
                time.sleep(0.5)
                tuner.pitch_detector.frequency_readings.clear()
                time.sleep(0.3)
                frequencies = [f for f, _ in tuner.pitch_detector.frequency_readings]
                frequency = float(np.nanmean(frequencies))
                positions_and_frequencies.append((mc0.cur_steps, frequency))
                print((mc0.cur_steps, frequency))

                if len(positions_and_frequencies) > 50:
                    print("This is taking too long, aborting...")
                    break

                if np.isnan(frequency):
                    # No reading, we don't know if we've reached the frequency
                    continue
                elif steps_per_move > 0 and frequency > target_frequency:
                    # Going up
                    break
                elif steps_per_move < 0 and frequency < target_frequency:
                    # Going down
                    break

            return positions_and_frequencies

        measurements = []
        for target_note, steps_per_move in [
            ("B3", 400),
            ("B2", -400),
            ("B3", 400),
            ("B2", -400),
        ]:
            measurements.append(
                go_to_frequency_and_measure(
                    float(librosa.note_to_hz(target_note)),
                    steps_per_move=steps_per_move,
                )
            )
        all_measurements = [
            (steps, freq) for steps, freq in sum(measurements, []) if not np.isnan(freq)
        ]
        print(all_measurements)

        time.sleep(3)

        tuner_strategy = ModelBasedTunerStrategy.from_readings(all_measurements)
        print(f"Model parameters: {tuner_strategy.coef=} {tuner_strategy.intercept=}")

        # notes = ["B2", "C3", "D3", "E3", "F3", "G3", "A3", "B3"]
        notes = ["B2", "C#3", "D#3", "E3", "F#3", "G#3", "A#3", "B3"]
        for it in range(2):
            notes += notes

        strumming_measurements = []

        for note in notes:
            hz = float(librosa.note_to_hz(note))
            steps = tuner_strategy.get_target_steps(hz)

            mc0.set_target_steps(steps, wait=True)
            strummer.strum()
            time.sleep(0.5)
            tuner.pitch_detector.frequency_readings.clear()
            time.sleep(0.3)
            frequencies = [f for f, _ in tuner.pitch_detector.frequency_readings]
            frequency = float(np.nanmean(frequencies))

            if not np.isnan(frequency):
                offset_octaves = librosa.hz_to_octs(frequency) - librosa.hz_to_octs(hz)
                offset_cents = int(offset_octaves * 1200)
            else:
                offset_cents = np.nan

            strumming_measurement = (note, steps, hz, frequency, offset_cents)
            strumming_measurements.append(strumming_measurement)
            print(strumming_measurement)

        print(strumming_measurements)


if __name__ == "__main__":
    main()
