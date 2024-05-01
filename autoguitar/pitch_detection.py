import time
from typing import Any

import librosa
import numpy as np
import sounddevice as sd  # pyright: ignore[reportMissingTypeStubs]

from autoguitar.virtual_string import VirtualString

duration = 30  # seconds


with VirtualString() as vs:
    last_freq = 0

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
            sr=48000.0,
        )
        # print(indata[:10, 0])
        freq = f0[1]
        if not np.isnan(f0[1]) and 100 < freq < 10000:
            vs.set_frequency(f0[1])
            print(" " * int((freq - 100) // 2), "*")
        else:
            print()

        with open("indata.npy", "wb") as f:
            np.save(f, indata)

    with sd.InputStream(callback=input_callback, blocksize=1024) as in_stream:
        print("Sample rate:", in_stream.samplerate)

        t1 = time.time()
        vs.set_frequency(1000)
        while time.time() - t1 < duration:
            time.sleep(0.3)
            vs.pluck()
