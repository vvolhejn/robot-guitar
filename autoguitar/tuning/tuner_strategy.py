import logging
from abc import ABC, abstractmethod
from collections import deque
from typing import Deque

import numpy as np
from sklearn.linear_model import LinearRegression

from autoguitar.dsp.pitch_detector import Timestamp

logger = logging.getLogger(__name__)


class TunerStrategy(ABC):
    @abstractmethod
    def get_target_steps(
        self,
        frequency: float,
        target_frequency: float,
        timestamp: Timestamp,
        cur_steps: int,
    ) -> int:
        """Calculate the target number of steps to set for the motor."""


class ProportionalTunerStrategy(TunerStrategy):
    def __init__(self, max_n_steps: int, speed: float, max_error_cents: float = 10):
        self.max_n_steps = max_n_steps
        self.speed = speed
        self.max_error_cents = max_error_cents

        if max_error_cents < 0:
            raise ValueError("max_error_cents must be non-negative")

    def get_target_steps(
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

        if (
            cents_to_frequency_ratio(-self.max_error_cents)
            < frequency / target_frequency
            < cents_to_frequency_ratio(self.max_error_cents)
        ):
            return cur_steps

        abs_n_steps = np.round(delta * self.speed)
        max_n_steps = self.max_n_steps
        abs_n_steps = int(np.clip(abs_n_steps, 1, max_n_steps))

        return cur_steps + sign * abs_n_steps


class ModelBasedTunerStrategy(TunerStrategy):
    def __init__(
        self,
        coef: float = 13.5,
        intercept: float | None = None,
        slack_correction_cents: int = 0,
        adaptiveness: float = 0.8,
    ):
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
            slack_correction_cents: Correct for the fact that the string has some
                slack by intentionally over-winding when going up in frequency and
                under-winding when going down.
            adaptiveness: How quickly to change the model parameters based on new
                incoming readings. From 0 to 1, where 0 means never change and 1
                means always use the last estimate.
        """
        self.readings: Deque[tuple[float, int, Timestamp]] = deque(maxlen=10)
        self.cooldown_until: float | None = None

        # If the coefficient is too low, the tuner will *overshoot*.
        self.coef: float = coef
        self.intercept: float | None = intercept
        self.slack_correction_cents = slack_correction_cents
        self.adaptiveness = adaptiveness

    @classmethod
    def from_readings(
        cls,
        readings: list[tuple[int, float]],
        coef: float | None = None,
        slack_correction_cents: int = 0,
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
            return cls(
                coef=model.coef_[0],
                intercept=float(model.intercept_),
                slack_correction_cents=slack_correction_cents,
            )
        else:
            intercepts = [freq**2 - steps * coef for steps, freq in readings]
            # Taking the mean minimizes the square error, so this is consistent with
            # the linear regression above.
            intercept = float(np.mean(intercepts))
            return cls(
                coef=coef,
                intercept=intercept,
                slack_correction_cents=slack_correction_cents,
            )

    def estimate_intercept(self) -> float | None:
        if len(self.readings) < 5:
            # Wait until we have a good number of readings for an accurate estimate
            return

        estimates = [
            frequency**2 - self.coef * cur_steps
            for frequency, cur_steps, _ in self.readings
        ]
        return float(np.median(estimates))

    def get_target_steps_raw(
        self, target_frequency: float, *, with_slack_correction: bool
    ) -> int:
        current_intercept = self.estimate_intercept()

        if self.intercept is None:
            if current_intercept is None:
                return 0  # Wait for more readings
            self.intercept = current_intercept
        else:
            print(f"{self.intercept=:.2f} vs {current_intercept=:.2f}")

            if (
                current_intercept is not None
                # TODO: more robust filtering of outliers. Generally we get these
                #   when the string is moving a lot.
                and abs(self.intercept - current_intercept) < 2000
            ):
                self.intercept = (
                    1 - self.adaptiveness
                ) * self.intercept + self.adaptiveness * current_intercept
            else:
                logger.warning(
                    "Intercept changed too much, skipping update: "
                    f"{self.intercept=:.2f} vs {current_intercept=:.2f}"
                )

        if with_slack_correction:
            target_frequency = self._correct_for_slack(
                target_frequency, target_frequency
            )

        estimated_target_steps = (1 / self.coef) * (
            target_frequency**2 - self.intercept
        )
        # print(intercept, estimated_target_steps)

        return int(estimated_target_steps)

    def get_target_steps(
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

        target_steps = self.get_target_steps_raw(
            target_frequency, with_slack_correction=True
        )

        return int(target_steps)

    def _correct_for_slack(
        self,
        frequency: float,
        target_frequency: float,
    ) -> float:
        """Correct for the fact that the string has some slack.

        Setting the same target_steps from above and below will result in
        different frequencies. I think this is because of the mechanical setup:
        the string is squeezed by the wood and this makes it not reach the
        frequency it's "supposed to". So if you go from below, the actual
        frequency is a little higher, and vice versa.
        """
        distance_cents = 1200 * np.log2(target_frequency / frequency)
        going_up = distance_cents > 0

        correction_coef = cents_to_frequency_ratio(self.slack_correction_cents)

        if going_up:  # intentionally over-wind
            target_frequency *= correction_coef
        else:  # intentionally under-wind
            target_frequency /= correction_coef

        return target_frequency

    def __repr__(self) -> str:
        return f"ModelBasedTunerStrategy(coef={self.coef}, intercept={self.intercept})"


def cents_to_frequency_ratio(cents: float) -> float:
    """Convert a number of cents to a frequency ratio.

    Answers the question "if I want to change the frequency by X cents, what do I have
    to multiple my current frequency by?".

    >>> cents_to_frequency_coef(1200)
    2.0
    >>> cents_to_frequency_coef(0)
    1.0
    >>> cents_to_frequency_coef(-1200)
    0.5
    >>> cents_to_frequency_coef(100)  # one semitone
    1.05946309436
    """
    return 2 ** (cents / 1200)
