import logging
import sys
import time
from collections import deque
from copy import deepcopy
from types import TracebackType
from typing import Any, Deque

import numpy as np
import sounddevice as sd  # pyright: ignore[reportMissingTypeStubs]
from pydantic import BaseModel

from autoguitar.signal import Signal

Timestamp = float  # A result of time.time()

logger = logging.getLogger(__name__)


class InputStreamCallbackData(BaseModel):
    indata: np.ndarray
    frames: int
    timestamp: float
    status: sd.CallbackFlags

    model_config = {
        "arbitrary_types_allowed": True,  # for np.ndarray
    }


class AudioInputStream:
    def __init__(self, block_size: int = 512, wait_for_initialization: bool = True):
        self.stream = None
        self.block_size = block_size

        self.readings: Deque[InputStreamCallbackData] = deque(maxlen=100)
        self.on_reading: Signal[InputStreamCallbackData] = Signal()

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
        self, indata: np.ndarray, frames: int, time: Any, status: sd.CallbackFlags
    ):
        assert self.stream is not None, "Stream should be initialized"
        indata = indata.copy()
        # time = time.copy()
        status = deepcopy(status)
        data = InputStreamCallbackData(
            indata=indata,
            frames=frames,
            timestamp=time.inputBufferAdcTime,
            status=status,
        )
        self.readings.append(data)

        self.on_reading.notify(data)

    def wait_for_initialization(self):
        """Wait until the audio stream is initialized.

        I don't understand what's happening. The AudioInputStream seems to start giving
        results immediately, but initializing LoudnessDetector() makes it stop for several
        seconds, even though the constructor itself finishes instantly. Huh?
        """
        time.sleep(0.1)
        self.readings.clear()
        print(
            "Waiting for audio stream to initialize",
            end="",
            flush=True,
            file=sys.stderr,
        )
        while not self.readings:
            time.sleep(0.5)
            print(".", end="", flush=True, file=sys.stderr)
        print()
