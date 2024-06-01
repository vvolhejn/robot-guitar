from abc import ABC, abstractmethod

import numpy as np

from autoguitar.pitch_detector import PitchDetector


class TunerStrategy(ABC):
    @abstractmethod
    def get_steps_to_move(
        self,
        frequency: float,
        target_frequency: float,
        pitch_detector: PitchDetector,
        cur_steps: int,
    ) -> int:
        """Calculate the relative number of steps to move the motor."""


class ProportionalTunerStrategy(TunerStrategy):
    def __init__(self):
        self.max_relative_error = 0.005
        self.max_n_steps = 50

    def get_steps_to_move(
        self,
        frequency: float,
        target_frequency: float,
        pitch_detector: PitchDetector,
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

        speed = 1.0
        abs_n_steps = np.round(delta * speed)
        max_n_steps = self.max_n_steps
        abs_n_steps = int(np.clip(abs_n_steps, 1, max_n_steps))

        return sign * abs_n_steps
