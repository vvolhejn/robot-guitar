import logging
from abc import ABC, abstractmethod
from collections import deque
from typing import Deque

import numpy as np

from autoguitar.pitch_detector import PitchDetector, Timestamp

logger = logging.getLogger(__name__)


class TunerStrategy(ABC):
    @abstractmethod
    def get_steps_to_move(
        self,
        frequency: float,
        target_frequency: float,
        timestamp: Timestamp,
        cur_steps: int,
    ) -> int:
        """Calculate the relative number of steps to move the motor."""


class ProportionalTunerStrategy(TunerStrategy):
    def __init__(
        self, max_n_steps: int, speed: float, max_relative_error: float = 0.005
    ):
        self.max_n_steps = max_n_steps
        self.speed = speed
        self.max_relative_error = max_relative_error

    def get_steps_to_move(
        self,
        frequency: float,
        target_frequency: float,
        timestamp: Timestamp,
        cur_steps: int,
    ) -> int:
        if np.isnan(frequency):
            raise ValueError("Frequency is NaN")

        delta = frequency - target_frequency
        sign = -int(np.sign(delta))
        delta = np.abs(delta)

        relative_error = delta / target_frequency
        if relative_error < self.max_relative_error:
            return 0

        abs_n_steps = np.round(delta * self.speed)
        max_n_steps = self.max_n_steps
        abs_n_steps = int(np.clip(abs_n_steps, 1, max_n_steps))

        return sign * abs_n_steps


class ModelBasedTunerStrategy(TunerStrategy):
    def __init__(self):
        self.readings: Deque[tuple[float, int, Timestamp]] = deque()
        self.max_readings = 10
        self.cooldown_until: float | None = None

        # Found using manual tuning on the physical string.
        # TODO: Find this automatically.
        self.coef = 85.0

    def estimate_intecept(self) -> float:
        estimates = [
            frequency**2 - self.coef * cur_steps
            for frequency, cur_steps, _ in self.readings
        ]
        return float(np.median(estimates))

    def get_steps_to_move(
        self,
        frequency: float,
        target_frequency: float,
        timestamp: Timestamp,
        cur_steps: int,
    ) -> int:
        if np.isnan(frequency):
            raise ValueError("Frequency is NaN")

        if self.cooldown_until is not None and timestamp < self.cooldown_until:
            return 0

        self.readings.append((frequency, cur_steps, timestamp))
        if len(self.readings) > self.max_readings:
            self.readings.popleft()

        intercept = self.estimate_intecept()

        estimated_target_steps = (1 / self.coef) * (target_frequency**2 - intercept)
        print(intercept, estimated_target_steps - cur_steps)

        # self.cooldown_until = timestamp + 2

        return int(estimated_target_steps - cur_steps)
