import logging
import time
from typing import Literal

import numpy as np
from pydantic import BaseModel

from autoguitar.dsp.input_stream import InputStream
from autoguitar.dsp.loudness_detector import LoudnessDetector
from autoguitar.motor import MotorController


class Calibration(BaseModel):
    low_loudness: float
    high_loudness: float
    downstroke_steps: int
    upstroke_steps: int


logger = logging.getLogger(__name__)


StrumState = Literal[
    "unknown",
    "upstroke",
    "upstroke_mute",
    "downstroke",
    "downstroke_mute",
]


class Strummer:
    def __init__(self, input_stream: InputStream, motor_controller: MotorController):
        self.input_stream = input_stream
        self.loudness_detector = LoudnessDetector(input_stream=input_stream)
        self.motor_controller = motor_controller

        # self.input_stream.on_reading.subscribe(self._input_stream_callback)

        self.calibration: Calibration | None = None
        self.strum_state: StrumState = "unknown"

    def calibrate(self):
        self.input_stream.wait_for_initialization()

        low_loudness, high_loudness = self._calibrate_loudness()
        loudness_difference = high_loudness - low_loudness

        # Moving by small steps is slow, so first take big steps to roughly
        # find where the string is
        time.sleep(0.5)
        self.find_strum_position(
            loudness_difference=loudness_difference, steps_at_a_time=-100
        )
        # Go a bit back
        self.motor_controller.move(-10, wait=True)
        time.sleep(1)

        # Now move in small steps until the string is plucked
        position_up = self.find_strum_position(
            loudness_difference=loudness_difference, steps_at_a_time=10
        )
        print("Upstroke position:", position_up)
        self.motor_controller.move(-30, wait=True)
        time.sleep(1)
        position_down = self.find_strum_position(
            loudness_difference=loudness_difference, steps_at_a_time=-10
        )
        print("Downstroke position:", position_down)

        self.calibration = Calibration(
            low_loudness=low_loudness,
            high_loudness=high_loudness,
            downstroke_steps=position_down,
            upstroke_steps=position_up,
        )
        self.strum_state = "downstroke"

    def _calibrate_loudness(self, min_readings: int = 2) -> tuple[float, float]:
        """Measure the loudness of the string when it is not plucked vs when it is."""
        # Note that we assume that there is silence at the beginning.
        low_loudness = self.loudness_detector.measure_loudness()

        # Do two full rotations to ensure we get enough data where the string is plucked
        self.loudness_detector.readings.clear()
        self.motor_controller.move(
            self.motor_controller.steps_per_turn() * 2, wait=True
        )

        # To remove potential outliers, take the 0.9 quantile.
        high_loudness = float(
            np.quantile(
                [loudness for loudness, _ in self.loudness_detector.readings], q=0.9
            )
        )

        logger.info(f"Silence loudness: {low_loudness:.4f} units")
        logger.info(f"Plucking loudness: {high_loudness:.4f} units")

        return low_loudness, high_loudness

    def find_strum_position(
        self, loudness_difference: float, steps_at_a_time: int
    ) -> int:
        last_loudness = self.loudness_detector.measure_loudness()

        while True:
            self.motor_controller.move(steps_at_a_time, wait=True)
            loudness2 = self.loudness_detector.measure_loudness(min_readings=5)
            loudness1 = last_loudness

            normalized_difference = (loudness2 - loudness1) / loudness_difference
            # print(f"{loudness1:.4f} {loudness2:.4f} {normalized_difference:.4f}")
            last_loudness = loudness2

            if normalized_difference > 0.3:
                # print("Plucked!")
                break

        return self.motor_controller.get_target_steps()

    def strum(self) -> None:
        target_state: dict[StrumState, StrumState] = {
            "upstroke": "downstroke",
            "upstroke_mute": "downstroke",
            "downstroke": "upstroke",
            "downstroke_mute": "upstroke",
        }
        self.set_strum_state(target_state[self.strum_state])

    def mute(self) -> None:
        target_state: dict[StrumState, StrumState] = {
            "upstroke": "upstroke_mute",
            "upstroke_mute": "upstroke_mute",
            "downstroke": "downstroke_mute",
            "downstroke_mute": "downstroke_mute",
        }
        self.set_strum_state(target_state[self.strum_state])

    def set_strum_state(self, state: StrumState) -> None:
        assert state != "unknown"
        self.motor_controller.set_target_steps(self._get_target_steps(state), wait=True)
        self.strum_state = state

    def _get_target_steps(self, state: StrumState) -> int:
        if self.calibration is None:
            raise ValueError("Calibrate the strummer first.")

        # What's tricky here is that the angle that you need to rotate depends
        # on the tension of the string. A loose string (lower frequency) will be
        # held longer by the pick, meaning you need to turn more for the pluck
        # to happen.
        return {
            "upstroke": self.calibration.upstroke_steps + 20,
            "upstroke_mute": self.calibration.downstroke_steps + 20,
            "downstroke": self.calibration.downstroke_steps - 30,
            "downstroke_mute": self.calibration.downstroke_steps + 25,
        }[state]
