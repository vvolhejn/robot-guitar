import time

import numpy as np

from autoguitar.motor import MotorController
from autoguitar.pitch_detector import PitchDetector, Timestamp


class Tuner:
    def __init__(
        self,
        pitch_detector: PitchDetector,
        motor_controller: MotorController,
        initial_target_frequency: float = 100,
    ):
        self.pitch_detector = pitch_detector
        self.motor_controller = motor_controller
        self.target_frequency = initial_target_frequency

        pitch_detector.on_reading.subscribe(self.on_pitch_reading)

    def on_pitch_reading(self, data: tuple[float, Timestamp]):
        frequency, timestamp = data
        reading_age = time.time() - timestamp
        if reading_age > 0.1:
            frequency = np.nan

        if np.isnan(frequency):
            return

        if self.motor_controller.is_moving():
            print("Still moving, skipping...")
            return

        n_steps = get_n_steps(frequency, self.target_frequency)
        print(
            f"Frequency: {frequency:.2f} Hz, "
            f"Target: {self.target_frequency:.2f} Hz, "
            f"Steps: {n_steps}"
        )
        self.motor_controller.move(n_steps)


def get_n_steps(frequency: float, target_frequency: float) -> int:
    """Calculate the number of steps to move the motor."""
    if np.isnan(frequency):
        raise ValueError("Frequency is NaN")

    delta = frequency - target_frequency
    sign = -int(np.sign(delta))
    delta = np.abs(delta)

    speed = 0.5
    abs_n_steps = np.round(delta * speed)
    max_n_steps = 30
    abs_n_steps = int(np.clip(abs_n_steps, 1, max_n_steps))

    return sign * abs_n_steps
