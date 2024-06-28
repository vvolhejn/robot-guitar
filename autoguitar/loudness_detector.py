import logging
import time
from collections import deque
from typing import Deque

import librosa
import numpy as np

from autoguitar.dsp.audio_input_stream import AudioInputStream, InputStreamCallbackData

Timestamp = float  # A result of time.time()

logger = logging.getLogger(__name__)


class LoudnessDetector:
    def __init__(self, audio_input_stream: AudioInputStream):
        self.audio_input_stream = audio_input_stream
        self.audio_input_stream.on_reading.subscribe(self._input_stream_callback)
        self.readings: Deque[tuple[float, Timestamp]] = deque(maxlen=100)

    def _input_stream_callback(self, callback_data: InputStreamCallbackData):
        timestamp = callback_data.timestamp
        loudness = librosa.feature.rms(y=callback_data.indata[:, 0]).mean()
        self._add_reading(loudness, timestamp)

    def _add_reading(self, loudness: float, timestamp: float):
        self.readings.append((loudness, timestamp))

    def get_mean_loudness(self) -> float:
        return float(np.mean([loudness for loudness, _ in self.readings]))

    def measure_loudness(self, min_readings: int = 2) -> float:
        self.readings.clear()
        while len(self.readings) < min_readings:
            time.sleep(0.001)
        return self.get_mean_loudness()
