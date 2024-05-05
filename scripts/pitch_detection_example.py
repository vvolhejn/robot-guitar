import time

import numpy as np

from autoguitar.pitch_detector import PitchDetector
from autoguitar.virtual_string import VirtualString

duration = 30  # seconds


with VirtualString() as virtual_string:
    with PitchDetector() as pitch_detector:
        t1 = time.time()
        while time.time() - t1 < duration:
            freq, _ = pitch_detector.get_frequency()

            if not np.isnan(freq) and 100 < freq < 10000:
                virtual_string.set_frequency(freq)
                print(" " * int((freq - 100) // 2), "*")
            else:
                print()
            time.sleep(0.3)
            virtual_string.pluck()
