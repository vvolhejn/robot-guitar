import logging
import threading
from pathlib import Path
from types import TracebackType

import soundfile as sf

from autoguitar.dsp.input_stream import InputStream, InputStreamCallbackData

logger = logging.getLogger(__name__)


class AudioRecorder:
    def __init__(self, path: str | Path, input_stream: InputStream):
        self.input_stream = input_stream
        self.path = path

    def __enter__(self):
        assert self.input_stream.stream is not None, "Expected initialized stream"

        sr = self.input_stream.stream.samplerate
        assert int(sr) == sr, "Expected integer samplerate"

        self.file = sf.SoundFile(
            self.path,
            mode="w",
            samplerate=int(sr),
            channels=self.input_stream.stream.channels,
        )
        self.file.__enter__()
        self.input_stream.on_reading.subscribe(self._on_reading)

        return self

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: TracebackType):
        self.file.__exit__()
        self.input_stream.on_reading.unsubscribe(self._on_reading)

    def _on_reading(self, data: InputStreamCallbackData):
        if self.file.closed:
            return

        if data.status.input_overflow or data.status.input_underflow:
            # Overflow is an issue because it means we are losing data.
            # Not sure about underflow.
            logger.warning(f"Error status: {data.status}")

        self.file.write(data.indata.copy())
