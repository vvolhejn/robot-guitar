import logging
from abc import ABC, abstractmethod
from collections import deque
from typing import Deque

import numpy as np
from sklearn.linear_model import LinearRegression, RANSACRegressor

from autoguitar.dsp.pitch_detector import Timestamp

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
    def __init__(self, coef: float = 13.5, intercept: float | None = None):
        """Tune the string using a model that estimates the rotation -> Hz function.

        The frequency of the string is proportional to the square root of the tension,
        and therefore also of the rotation:
            f^2 = coef*x + intercept
        where f is the frequency, x is the rotation (#steps relative to some
        initial angle), and coef and intercept are parameters of the linear
        model. We estimate these from the data. Once we've fixed the parameters,
        we can compute the rotation needed to reach a given frequency:
            x = (1/coef)*(f^2 - intercept)

        Args:
            coef: The coefficient of the model, see above.
            intercept: The intercept of the model, see above. If None, will be
                computed dynamically based on readings from the pitch
                detector. This is useful because with fixed parameters, the
                model can become inaccurate after some time.
        """
        self.readings: Deque[tuple[float, int, Timestamp]] = deque(maxlen=10)
        self.cooldown_until: float | None = None

        # Found using manual tuning on the physical string.
        # TODO: Find this automatically.
        # If the coefficient is too low, the tuner will *overshoot*.
        self.coef: float = coef
        self.intercept: float | None = intercept

    @classmethod
    def from_readings(
        cls, readings: list[tuple[int, float]], coef: float | None = None
    ):
        """Estimate the model parameters from (steps, frequency) pairs.

        Args:
            coef: If given, use this as the coefficient of the model and only fit
                the intercept. This requires less data but might be less accurate.
                Otherwise, estimate the coefficient as well.
        """
        if coef is None:
            model = LinearRegression()
            X = np.array([steps for steps, _ in readings])[:, np.newaxis]
            # We fit the model to f^2 = coef*x + intercept, see __init__.
            y = np.array([freq**2 for _, freq in readings])
            model.fit(X, y)
            return cls(coef=model.coef_[0], intercept=float(model.intercept_))
        else:
            intercepts = [freq**2 - steps * coef for steps, freq in readings]
            # Taking the mean minimizes the square error, so this is consistent with
            # the linear regression above.
            intercept = float(np.mean(intercepts))
            return cls(coef=coef, intercept=intercept)

    def estimate_intecept(self) -> float:
        estimates = [
            frequency**2 - self.coef * cur_steps
            for frequency, cur_steps, _ in self.readings
        ]
        return float(np.median(estimates))

    def get_target_steps(self, target_frequency: float) -> int:
        if self.intercept is None:
            intercept = self.estimate_intecept()
        else:
            intercept = self.intercept

        estimated_target_steps = (1 / self.coef) * (target_frequency**2 - intercept)
        # print(intercept, estimated_target_steps)

        return int(estimated_target_steps)

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

        # Old readings get removed by the queue's maxlen
        self.readings.append((frequency, cur_steps, timestamp))

        estimated_target_steps = self.get_target_steps(target_frequency)

        return int(estimated_target_steps - cur_steps)

    def __repr__(self) -> str:
        return f"ModelBasedTunerStrategy(coef={self.coef}, intercept={self.intercept})"
