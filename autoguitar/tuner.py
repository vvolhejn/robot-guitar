import sys
import time

import numpy as np
import requests

from autoguitar.motor import MotorController
from autoguitar.pitch_detector import PitchDetector, Timestamp
from autoguitar.tuner_strategy import ProportionalTunerStrategy, TunerStrategy


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
        self.tuner_strategy: TunerStrategy = ProportionalTunerStrategy()

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

        n_steps = self.tuner_strategy.get_steps_to_move(
            frequency,
            self.target_frequency,
            self.pitch_detector,
            self.motor_controller.cur_steps,
        )

        self.send_update_to_server(frequency=frequency, n_steps=n_steps)

        self.motor_controller.move(n_steps)

    def send_update_to_server(self, frequency: float, n_steps: int):
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
