import logging
import time
from typing import Literal

import numpy as np
from pydantic import BaseModel

from autoguitar.dsp.input_stream import InputStream
from autoguitar.dsp.loudness_detector import LoudnessDetector
from autoguitar.motor import AbstractMotorController


class Calibration(BaseModel):
    # Not sure we actually need the loudness measurements.
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

STROKE_DISTANCE = 50
UPSTROKE_BASE_OFFSET = 15


class Strummer:
    def __init__(
        self, input_stream: InputStream, motor_controller: AbstractMotorController
    ):
        self.input_stream = input_stream
        self.loudness_detector = LoudnessDetector(input_stream=input_stream)
        self.motor_controller = motor_controller
        self.downstroke_offset = 0
        self.upstroke_offset = 0

        # self.input_stream.on_reading.subscribe(self._input_stream_callback)

        self.calibration: Calibration | None = None
        self.strum_state: StrumState = "unknown"

    def calibrate(self, estimate_downstroke_separately: bool = False):
        """Measure the motor positions for the upstroke and downstroke.

        Args:
            estimate_downstroke_separately: If False, do a rough estimate
                of the downstroke position based on the upstroke position.
                Faster but potentially less accurate.
        """
        self.input_stream.wait_for_initialization()

        low_loudness = self.loudness_detector.measure_loudness()
        print("Low loudness: ", low_loudness)

        # Moving by small steps is slow, so first take big steps to roughly
        # find where the string is
        time.sleep(0.5)
        self.find_strum_position(steps_at_a_time=-25)
        high_loudness = self.loudness_detector.measure_loudness()
        # Go a bit back
        self.motor_controller.move(-10, wait=True)
        time.sleep(1)

        # Now move in small steps until the string is plucked
        position_up = self.find_strum_position(steps_at_a_time=3)
        position_up += UPSTROKE_BASE_OFFSET
        print("Upstroke position:", position_up)

        if estimate_downstroke_separately:
            self.motor_controller.move(-10, wait=True)
            time.sleep(1)
            position_down = self.find_strum_position(steps_at_a_time=-3)
            self.strum_state = "downstroke"
        else:
            # The angle difference should always be more or less the same
            position_down = position_up - STROKE_DISTANCE
            self.strum_state = "upstroke"

        print("Downstroke position:", position_down)

        self.calibration = Calibration(
            low_loudness=low_loudness,
            high_loudness=high_loudness,
            downstroke_steps=position_down,
            upstroke_steps=position_up,
        )
        self.set_strum_state("upstroke")

    def _calibrate_loudness(self, min_readings: int = 2) -> tuple[float, float]:
        """Measure the loudness of the string when it is not plucked vs when it is."""
        # Note that we assume that there is silence at the beginning.
        low_loudness = self.loudness_detector.measure_loudness()

        # Do two full rotations to ensure we get enough data where the string is plucked
        self.loudness_detector.readings.clear()
        self.motor_controller.move(
            self.motor_controller.steps_per_turn() * 2, wait=True
        )
        time.sleep(1)

        # To remove potential outliers, take the 0.9 quantile.
        high_loudness = float(
            np.quantile(
                [loudness for loudness, _ in self.loudness_detector.readings], q=0.9
            )
        )

        logger.info(f"Silence loudness: {low_loudness:.4f} units")
        logger.info(f"Plucking loudness: {high_loudness:.4f} units")

        return low_loudness, high_loudness

    def find_strum_position(self, steps_at_a_time: int) -> int:
        last_loudness = self.loudness_detector.measure_loudness()

        MIN_LOUDNESS_RATIO = 1.1

        while True:
            self.motor_controller.move(steps_at_a_time, wait=True)
            loudness2 = self.loudness_detector.measure_loudness(min_readings=3)
            loudness1 = last_loudness

            last_loudness = loudness2

            if loudness2 / loudness1 > MIN_LOUDNESS_RATIO:
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
            "upstroke": self.calibration.upstroke_steps + self.upstroke_offset,
            "downstroke": self.calibration.downstroke_steps + self.downstroke_offset,
            # unused atm:
            "upstroke_mute": self.calibration.downstroke_steps + 5,
            "downstroke_mute": self.calibration.downstroke_steps + 6,
        }[state]
