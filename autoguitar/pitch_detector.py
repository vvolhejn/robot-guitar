import time
from collections import deque
from types import TracebackType
from typing import Any, Deque

import librosa
import numpy as np
import sounddevice as sd  # pyright: ignore[reportMissingTypeStubs]

Timestamp = float  # A result of time.time()


class PitchDetector:
    def __init__(self):
        self.stream = sd.InputStream(callback=self._input_callback, blocksize=4096)
        self.frequency_readings: Deque[tuple[float, Timestamp]] = deque()
        self.max_readings = 10

    def __enter__(self):
        self.stream.__enter__()
        return self

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: TracebackType):
        self.stream.__exit__()

    def _input_callback(
        self, indata: np.ndarray, frames: int, time: Any, status: sd.CallbackFlags
    ):
        f0, _voiced_flag, _voiced_prob = librosa.pyin(
            indata[:, 0],
            # float() is just to make Pyright happy
            fmin=float(librosa.note_to_hz("C2")),
            fmax=float(librosa.note_to_hz("C7")),
            sr=self.stream.samplerate,
        )

        freq: float = np.nan
        if not np.isnan(f0).all():
            # If some of the frames came out as non-nan, take the mean of those
            freq = float(np.nanmean(f0))

        self._add_reading(freq)

    def _add_reading(self, freq: float):
        self.frequency_readings.append((freq, time.time()))
        if len(self.frequency_readings) > self.max_readings:
            self.frequency_readings.popleft()

    def get_frequency(self) -> tuple[float, Timestamp]:
        print(list(self.frequency_readings))
        if not self.frequency_readings:
            return (np.nan, 0)
        else:
            return self.frequency_readings[-1]
