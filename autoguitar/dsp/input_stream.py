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


class InputStream:
    def __init__(self, block_size: int):
        self.stream = None

        # check that block_size is a power of 2
        if block_size & (block_size - 1) != 0:
            raise ValueError("block_size should be a power of 2")

        self.block_size = block_size

        self.readings: Deque[InputStreamCallbackData] = deque()
        # In __enter__, we set a max length on the deque to enforce `history_sec``
        self.history_sec = 1.0

        self.on_reading: Signal[InputStreamCallbackData] = Signal()

    def __enter__(self):
        self.stream = sd.InputStream(
            callback=self._input_stream_callback, blocksize=self.block_size
        )
        self.stream.__enter__()
        blocks_per_sec = self.stream.samplerate / self.block_size
        self.readings = deque(maxlen=int(self.history_sec * blocks_per_sec))

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

    def get_latest_audio(self, max_n_samples: int) -> np.ndarray:
        """Get the latest audio samples.

        Useful if you need a longer sample than the block size.

        Args:
            max_n_samples: Maximum number of samples to return. There might be
                fewer samples available.

        Returns:
            A 1D numpy array with the latest audio samples.
        """
        y = np.concatenate([data.indata[:, 0] for data in self.readings])
        return y[-max_n_samples:]
