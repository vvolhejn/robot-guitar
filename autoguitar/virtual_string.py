import time

import numpy as np
import sounddevice as sd


class VirtualString:
    def __init__(self):
        self.last_time_sec = 0
        self.pluck_time_sec = -100
        self._frequency = 440
        self.sample_rate = 44100
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate, channels=1, callback=self._audio_callback
        )

    def pluck(self):
        self.pluck_time_sec = self.last_time_sec

    def set_frequency(self, frequency: int):
        if frequency < 100 or frequency > 10000:
            raise ValueError("Frequency must be between 100 and 10000 Hz")
        self._frequency = frequency

    def _audio_callback(self, outdata, frames, time, status):
        def decay(t, pluck_time):
            half_time_sec = 0.5
            delta_time = t - pluck_time
            return np.exp(delta_time * np.log(0.5) / half_time_sec)

        # Shift the time so that the phase is continuous
        t = (
            np.arange(frames) + time.outputBufferDacTime * self.sample_rate
        ) / self.sample_rate

        outdata[:, 0] = (
            0.5
            * np.sin(2 * np.pi * self._frequency * t).astype(np.float32)
            * decay(t, self.pluck_time_sec)
        )

        self.last_time_sec = time.outputBufferDacTime

    def __enter__(self):
        self.stream.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
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
