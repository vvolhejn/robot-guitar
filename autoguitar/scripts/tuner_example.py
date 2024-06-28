import time

from autoguitar.dsp.pitch_detector import PitchDetector, Timestamp
from autoguitar.motor import MotorController, get_motor
from autoguitar.tuner import Tuner

n_steps = 0
desired_freq = 70
max_reading_age = 0.1


def run_tuner():
    motor = get_motor()
    with PitchDetector() as pitch_detector:
        with MotorController(motor=motor, max_steps=10000) as mc:
            tuner = Tuner(
                pitch_detector=pitch_detector,
                motor_controller=mc,
                initial_target_frequency=70,
            )

            def tuner_oscillate(data: tuple[float, Timestamp]):
                """Update the target frequency when the current target is reached.

                Oscillate between 70 and 140 Hz.
                """
                frequency, _timestamp = data

                goal_hit = abs(tuner.target_frequency - frequency) <= 1

                if goal_hit:
                    print("goal hit!", goal_hit, tuner.target_frequency, frequency)
                    if tuner.target_frequency == 70:
                        tuner.target_frequency = 140
                    else:
                        tuner.target_frequency = 70

            pitch_detector.on_reading.subscribe(tuner_oscillate)

            print("Starting (pitch detector takes a few seconds to start up)")
            while True:
                time.sleep(1)  # just to keep the thread alive.


if __name__ == "__main__":
    run_tuner()
