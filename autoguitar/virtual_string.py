import time
from types import TracebackType
from typing import Any

import numpy as np

# Weirdly, the generated stubs give less info than when we just keep it this way,
# e.g. `sd.CallbackFlags` is not recognized. Something to do with CFFI.
import sounddevice as sd  # pyright: ignore[reportMissingTypeStubs]


def remap(value: float, *, x1: float, x2: float, y1: float, y2: float):
    """Remap a value linearly from one range to another.

    If value=x1, the function returns y1. If value=x2, the function returns y2.
    """
    return y1 + (value - x1) * (y2 - y1) / (x2 - x1)


class Envelope:
    def __init__(self, attack_sec: float, decay_halftime_sec: float):
        self.attack_sec = attack_sec
        self.decay_halftime_sec = decay_halftime_sec

        self.pluck_time_sec = -100
        self.stop_time_sec = None
        self.pluck_start_volume = 0.0

    def pluck(self, t: float):
        self.pluck_start_volume = self(t)
        self.pluck_time_sec = t

    def __call__(self, t: float):
        time_since_pluck = t - self.pluck_time_sec

        if time_since_pluck < 0:
            return 0

        if time_since_pluck < self.attack_sec:
            # Attack
            return remap(
                time_since_pluck,
                x1=0,
                x2=self.attack_sec,
                y1=self.pluck_start_volume,
                y2=1,
            )
        else:
            # Decay
            return np.exp(
                -(time_since_pluck - self.attack_sec)
                / self.decay_halftime_sec
                * np.log(2)
            )


class VirtualString:
    def __init__(self):
        self.last_time_sec = 0
        self.pluck_time_sec = -100
        self._frequency = 440.0
        self.sample_rate = 44100
        self.last_phase: float = 0.0
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=self._audio_callback,
            blocksize=4096,
        )
        self.envelope = Envelope(attack_sec=0.03, decay_halftime_sec=0.5)

    def pluck(self):
        self.envelope.pluck(self.last_time_sec)

    def set_frequency(self, frequency: float):
        if frequency < 100 or frequency > 10000:
            raise ValueError("Frequency must be between 100 and 10000 Hz")
        self._frequency = frequency

    def shift_frequency(self, shift: float):
        self.set_frequency(self._frequency + shift)

    def _audio_callback(
        self,
        outdata: np.ndarray,
        frames: int,
        time: Any,  # see sounddevice docs
        status: sd.CallbackFlags,
    ):
        # We compute the cumulative phase so that there isn't a "jump"
        # from one frame to another - that would cause a clicking sound.
        angular_freq = np.full(
            (frames,), 2 * np.pi * self._frequency / self.sample_rate
        )
        phase = np.cumsum(angular_freq) + self.last_phase

        # Shift the time so that the phase is continuous
        envelope_time = (
            np.arange(frames) + time.outputBufferDacTime * self.sample_rate
        ) / self.sample_rate

        envelope_value = [self.envelope(x) for x in envelope_time]
        assert (np.abs(envelope_value) <= 1).all()

        outdata[:, 0] = 0.1 * np.sin(phase).astype(np.float32) * envelope_value

        self.last_time_sec = time.outputBufferDacTime
        self.last_phase = phase[-1]

    def __enter__(self):
        self.stream.start()
        return self

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: TracebackType):
        self.stream.stop()
        self.stream.close()


if __name__ == "__main__":
    with VirtualString() as vs:
        # hack: small initial delay so that self.last_time is already initialized
        time.sleep(0.01)
        vs.pluck()
        while True:
            vs.set_frequency(440 + 440 * np.random.rand())
            time.sleep(0.2 * np.random.randint(1, 5))
            vs.pluck()
