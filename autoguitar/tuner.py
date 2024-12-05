import sys

import numpy as np
import requests

from autoguitar.dsp.input_stream import InputStream
from autoguitar.dsp.pitch_detector import PitchDetector, Timestamp
from autoguitar.motor import MotorController
from autoguitar.tuner_strategy import (
    ModelBasedTunerStrategy,
    TunerStrategy,
)


class Tuner:
    def __init__(
        self,
        input_stream: InputStream,
        motor_controller: MotorController,
        initial_target_frequency: float = 100,
        tuner_strategy: TunerStrategy | None = None,
    ):
        self.input_stream = input_stream
        self.pitch_detector = PitchDetector(input_stream=input_stream)
        self.motor_controller = motor_controller
        self.target_frequency = initial_target_frequency

        if tuner_strategy is None:
            # self.tuner_strategy: TunerStrategy = ProportionalTunerStrategy(
            #     max_n_steps=1000, speed=10.0
            # )
            self.tuner_strategy: TunerStrategy = ModelBasedTunerStrategy(
                coef=4.35,
                adaptiveness=0.5,
            )
        else:
            self.tuner_strategy = tuner_strategy

        self.pitch_detector.on_reading.subscribe(self.on_pitch_reading)

    def on_pitch_reading(self, data: tuple[float, Timestamp]):
        frequency, timestamp = data

        if np.isnan(frequency):
            return

        if self.motor_controller.is_moving():
            print("Still moving, skipping...", file=sys.stderr)
            return

        target_steps = self.tuner_strategy.get_target_steps(
            frequency,
            self.target_frequency,
            timestamp,
            self.motor_controller.cur_steps,
        )

        print(
            f"Frequency: {frequency:.2f} Hz,\t"
            f"Target frequency: {self.target_frequency:.2f} Hz,\t"
            f"Cur steps: {self.motor_controller.cur_steps},\t"
            f"Target steps: {target_steps},\t",
            file=sys.stderr,
        )

        # Disabled because we now run a server on the RPi side.
        # self.send_update_to_server(frequency=frequency, target_steps=target_steps)

        self.motor_controller.set_target_steps(target_steps)

    def send_update_to_server(self, frequency: float, target_steps: int):
        try:
            requests.post(
                "http://localhost:8050/api/event",
                json={
                    "kind": "tuner",
                    "value": {
                        "frequency": frequency,
                        "target_frequency": self.target_frequency,
                        "target_steps": target_steps,
                        "cur_steps": self.motor_controller.cur_steps,
                    },
                },
                timeout=1,
            )
        except requests.ConnectionError as e:
            print(e, file=sys.stderr)

    def unsubscribe(self):
        self.pitch_detector.on_reading.unsubscribe(self.on_pitch_reading)
