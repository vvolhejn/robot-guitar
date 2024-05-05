import time
from typing import Any

import librosa
import numpy as np
import sounddevice as sd  # pyright: ignore[reportMissingTypeStubs]

from autoguitar.virtual_string import VirtualString

duration = 30  # seconds


with VirtualString() as vs:
    last_freq = 0
    sample_rate = 48000.0  # Default, will be overwritten below

    def input_callback(
        indata: np.ndarray,
        frames: int,
        time: Any,
        status: sd.CallbackFlags,
    ):
        f0, _voiced_flag, _voiced_prob = librosa.pyin(
            indata[:, 0],
            # float() is just to make Pyright happy
            fmin=float(librosa.note_to_hz("C2")),
            fmax=float(librosa.note_to_hz("C7")),
            sr=sample_rate,
        )

        freq: float = np.nan
        if not np.isnan(f0).all():
            # If some of the frames came out as non-nan, take the mean of those
            freq = float(np.nanmean(f0))

        if not np.isnan(freq) and 100 < freq < 10000:
            vs.set_frequency(freq)
            # print(" " * int((freq - 100) // 2), "*")
        else:
            pass
            # print()

        print("freq", freq)

        # with open("indata.npy", "wb") as f:
        #     np.save(f, indata)

    with sd.InputStream(callback=input_callback, blocksize=4096) as in_stream:
        sample_rate = in_stream.samplerate

        t1 = time.time()
        vs.set_frequency(1000)
        while time.time() - t1 < duration:
            time.sleep(0.3)
            vs.pluck()
