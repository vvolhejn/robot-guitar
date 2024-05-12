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
        self.stream = None
        self.block_size = 4096
        self.frequency_readings: Deque[tuple[float, Timestamp]] = deque()
        self.max_readings = 10
        self.on_reading: Signal[tuple[float, Timestamp]] = Signal()

    def __enter__(self):
        self.stream = sd.InputStream(
            callback=self._input_stream_callback, blocksize=self.block_size
        )
        self.stream.__enter__()
        return self

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: TracebackType):
        assert self.stream is not None, "Stream should be initialized when exiting"
        self.stream.__exit__()

    def _input_stream_callback(
        self, indata: np.ndarray, frames: int, _time: Any, status: sd.CallbackFlags
    ):
        assert self.stream is not None, "Stream should be initialized"

        y = indata[:, 0]
        freq, _ = self.detect_pitch(y, sr=self.stream.samplerate)
        self._add_reading(freq)

    def detect_pitch(self, y: np.ndarray, *, sr: int) -> tuple[float, float]:
        """Estimate the fundamental frequency of the audio signal.

        We assume that the signal is short, so only a single frequency is returned.

        Returns:
            A (frequency, confidence) tuple. The confidence is a value between 0 and 1,
            the estimated fundamental frequency in Hz. NaN if no frequency was found.
        """
        assert y.ndim == 1, f"Expected 1D array, got shape {y.shape}"
        length_sec = len(y) / sr
        assert length_sec < 0.5, f"Expected short signal, got {length_sec:.2f}s"

        min_freq = float(librosa.note_to_hz("E1"))  # bass E
        # C4 is 261.63 Hz, more than we can currently wind the string to
        max_freq = float(librosa.note_to_hz("C4"))
        f0 = librosa.yin(y, fmin=min_freq, fmax=max_freq, sr=sr)

        # Sometimes we get incorrect readings close to the max frequency,
        # probably it's just because nothing is playing at the time and there's
        # noise
        f0[f0 >= 0.9 * max_freq] = np.nan

        if np.isnan(f0).all():
            return np.nan, 0
        else:
            freq = float(np.nanmedian(f0))
            is_outlier = np.isnan(f0) | (np.abs(f0 - freq) > 0.3 * freq)
            confidence = 1 - is_outlier.mean()

            # Heuristic - if there are multiple outliers, the reading is noisy
            if is_outlier.sum() > 1:
                return np.nan, confidence
            else:
                return freq, confidence

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
