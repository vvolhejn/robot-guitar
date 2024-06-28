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


class LoudnessDetector:
    def __init__(self):
        self.stream = None
        self.block_size = 512  # Doesn't matter too much here
        self.readings: Deque[tuple[float, Timestamp]] = deque()
        self.max_readings = 100
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
        timestamp = time.time()
        loudness = librosa.feature.rms(y=y).mean()
        self._add_reading(loudness, timestamp)

    def _add_reading(self, loudness: float, timestamp: float):
        self.readings.append((loudness, timestamp))
        if len(self.readings) > self.max_readings:
            self.readings.popleft()

        self.on_reading.notify((loudness, timestamp))

    def get_mean_loudness(self) -> float:
        return float(np.mean([loudness for loudness, _ in self.readings]))
