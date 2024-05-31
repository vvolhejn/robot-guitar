import sys
import time

import numpy as np
import requests

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
            print("Still moving, skipping...", file=sys.stderr)
            return

        n_steps = get_n_steps(frequency, self.target_frequency)
        self.post_update(frequency=frequency, n_steps=n_steps)

        self.motor_controller.move(n_steps)

    def post_update(self, frequency: float, n_steps: int):
        try:
            requests.post(
                "http://localhost:8050/api/event",
                json={
                    "kind": "tuner",
                    "value": {
                        "frequency": frequency,
                        "target_frequency": self.target_frequency,
                        "steps_to_move": n_steps,
                        "cur_steps": self.motor_controller.cur_steps,
                    },
                },
            )
        except requests.ConnectionError as e:
            print(e, file=sys.stderr)


def get_n_steps(frequency: float, target_frequency: float) -> int:
    """Calculate the number of steps to move the motor."""
    if np.isnan(frequency):
        raise ValueError("Frequency is NaN")

    delta = frequency - target_frequency
    sign = -int(np.sign(delta))
    delta = np.abs(delta)

    relative_error = delta / target_frequency
    if relative_error < 0.005:
        return 0

    speed = 1.0
    abs_n_steps = np.round(delta * speed)
    max_n_steps = 50
    abs_n_steps = int(np.clip(abs_n_steps, 1, max_n_steps))

    return sign * abs_n_steps
