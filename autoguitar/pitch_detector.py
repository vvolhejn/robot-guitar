import logging
import time
from collections import deque
from types import TracebackType
from typing import Any, Deque

import librosa
import numpy as np
import sounddevice as sd  # pyright: ignore[reportMissingTypeStubs]

from autoguitar.signal import Signal

Timestamp = float  # A result of time.time()

logger = logging.getLogger(__name__)


class PitchDetector:
    def __init__(self):
        self.stream = sd.InputStream(callback=self._input_callback, blocksize=4096)
        self.frequency_readings: Deque[tuple[float, Timestamp]] = deque()
        self.max_readings = 10
        self.on_reading: Signal[tuple[float, Timestamp]] = Signal()

    def __enter__(self):
        self.stream.__enter__()
        return self

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: TracebackType):
        self.stream.__exit__()

    def _input_callback(
        self, indata: np.ndarray, frames: int, _time: Any, status: sd.CallbackFlags
    ):
        # float() is just to make Pyright happy
        min_freq = float(librosa.note_to_hz("E1"))  # bass E
        # C4 is 261.63 Hz, more than we can currently wind the string to
        max_freq = float(librosa.note_to_hz("C4"))

        x = indata[:, 0]
        f0 = librosa.yin(x, fmin=min_freq, fmax=max_freq, sr=self.stream.samplerate)

        # Sometimes we get incorrect readings close to the max frequency,
        # probably it's just because nothing is playing at the time and there's
        # noise
        f0[f0 >= 0.9 * max_freq] = np.nan

        freq: float = np.nan
        if not np.isnan(f0).all():
            # If some of the frames came out as non-nan, take the mean of those
            # freq = float(np.nanmean(f0))
            freq = float(np.nanmedian(f0))

        self._add_reading(freq)

    def _add_reading(self, freq: float):
        timestamp = time.time()
        self.frequency_readings.append((freq, timestamp))
        if len(self.frequency_readings) > self.max_readings:
            self.frequency_readings.popleft()

        if not np.isnan(freq):
            logger.debug(f"Frequency: {freq:.2f} Hz")

        self.on_reading.notify((freq, timestamp))

    def get_frequency(self) -> tuple[float, Timestamp | None]:
        if not self.frequency_readings:
            return (np.nan, None)
        else:
            return self.frequency_readings[-1]
