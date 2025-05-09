import logging
import threading
from collections import deque
from queue import Empty, Full, Queue
from typing import Deque

import librosa
import numpy as np

from autoguitar.dsp.input_stream import InputStream, InputStreamCallbackData
from autoguitar.signal import Signal

Timestamp = float  # A result of time.time()

logger = logging.getLogger(__name__)


class PitchDetector:
    """A real-time pitch detector based on audio coming from an InputStream.

    Pitch detection is computationally expensive (for the Raspberry Pi) so we
    run it on a separate thread to avoid input overflow in the InputStream. That
    would mean some blocks would get discarded, which is bad mainly if you want
    to record the incoming audio into a file.
    """

    def __init__(self, input_stream: InputStream):
        self.input_stream = input_stream
        self.input_stream.on_reading.subscribe(self._input_stream_callback)

        self.frequency_readings: Deque[tuple[float, Timestamp]] = deque(maxlen=100)
        self.on_reading: Signal[tuple[float, Timestamp]] = Signal()
        self.n_samples_per_reading = 8192
        self.cooldown_until = 0

        # Run the pitch detection itself in a separate thread.
        # We don't care about processing all readings. If we can't keep up, process
        # only the latest one. Although note that _task_queue.put_nowait() will not
        # overwrite the existing reading,
        self._task_queue = Queue(maxsize=1)
        self.thread = threading.Thread(target=self._process_readings)
        self.thread.start()

    def _input_stream_callback(self, callback_data: InputStreamCallbackData):
        assert self.input_stream.stream is not None
        assert callback_data.timestamp >= 0, "Expected non-negative timestamp"
        timestamp = callback_data.timestamp

        if timestamp < self.cooldown_until:
            return

        # If the block size is small, this callback will get called very often.
        # Since it's cost-intensive, we want to throttle it a bit.
        cooldown_coef = 0.5  # Pause length relative to n_samples_per_reading
        self.cooldown_until = (
            timestamp
            + (self.n_samples_per_reading * cooldown_coef)
            / self.input_stream.stream.samplerate
        )

        # Pitch detection needs a bit more samples to work well, potentially more
        # than the block size
        y = self.input_stream.get_latest_audio(max_n_samples=self.n_samples_per_reading)
        if len(y) < self.n_samples_per_reading:
            # The Yin algorithm might fail if we try to run it on fewer samples with the
            # same parameters
            return

        try:
            self._task_queue.put_nowait((y, timestamp))
        except Full:
            # logger.warning("Pitch detector queue is full, skipping a reading")
            pass

    def _process_readings(self):
        while self.input_stream.stream is not None:
            try:
                y, timestamp = self._task_queue.get(timeout=0.5)
            except Empty:
                # If the input stream has ended, we should stop. We use the
                # timeout argument to ensure that the condition is re-checked
                continue

            sr = self.input_stream.stream.samplerate
            freq, _ = detect_pitch(y=y, sr=sr, use_pyin=True)

            if self.is_reading_plausible(freq, timestamp):
                self._add_reading(freq, timestamp)

    def is_reading_plausible(self, freq: float, timestamp: float) -> bool:
        """Check if a reading is plausible given past readings.

        The pitch detector commonly gives incorrect readings, especially ones
        that are off by an octave.
        """
        MAX_DELTA_HZ = 50
        MAX_DELTA_SEC_FOR_CHECK = 1.0

        if np.isnan(freq):
            return True

        last_valid_reading = None
        for reading in reversed(self.frequency_readings):
            if not np.isnan(reading[0]):
                last_valid_reading = reading
                break

        if last_valid_reading is not None:
            last_freq, last_timestamp = last_valid_reading
            delta_time = timestamp - last_timestamp
            delta_freq = np.abs(freq - last_freq)

            if delta_time < MAX_DELTA_SEC_FOR_CHECK and delta_freq > MAX_DELTA_HZ:
                logger.info(
                    "Frequency change too fast: "
                    f"from {last_freq:.2f} to {freq:.2f} Hz in {delta_time:.2f}s"
                )
                return False

            return True
        else:
            return True

    def _add_reading(self, freq: float, timestamp: float):
        # Old readings get removed by the queue's maxlen
        self.frequency_readings.append((freq, timestamp))

        if not np.isnan(freq):
            logger.debug(f"Frequency: {freq:.2f} Hz")

        self.on_reading.notify((freq, timestamp))

    def get_frequency(self) -> tuple[float, Timestamp | None]:
        if not self.frequency_readings:
            return (np.nan, None)
        else:
            return self.frequency_readings[-1]


def detect_pitch(
    y: np.ndarray,
    *,
    sr: int,
    use_pyin: bool,
    min_note: str = "E1",
    max_note: str = "E3",
) -> tuple[float, float]:
    """Estimate the fundamental frequency of the audio signal.

    We assume that the signal is short, so only a single frequency is returned.

    Returns:
        A (frequency, confidence) tuple. The confidence is a value between 0 and 1,
        the estimated fundamental frequency in Hz. NaN if no frequency was found.
    """
    assert y.ndim == 1, f"Expected 1D array, got shape {y.shape}"
    length_sec = len(y) / sr
    assert length_sec < 0.5, f"Expected short signal, got {length_sec:.2f}s"

    min_freq = float(librosa.note_to_hz(min_note))  # bass E
    # max_freq should be higher than we can currently wind the string to
    max_freq = float(librosa.note_to_hz(max_note))

    if use_pyin:
        f0, voiced, voiced_prob = librosa.pyin(
            y, fmin=min_freq, fmax=max_freq, sr=sr, frame_length=len(y) // 2
        )

        if f0[-1] >= 0.9 * max_freq:
            # Sometimes we get incorrect readings close to the max frequency,
            # probably it's just because nothing is playing at the time and there's
            # noise
            return np.nan, 0

        if voiced[-1]:
            return f0[-1], voiced_prob[-1]
        else:
            return np.nan, 0
    else:
        # YIN is faster but less accurate than pYIN. We apply more post-processing
        # to get a more accurate result.

        f0 = librosa.yin(
            y, fmin=min_freq, fmax=max_freq, sr=sr, frame_length=len(y) // 2
        )

        # Sometimes we get incorrect readings close to the max frequency,
        # probably it's just because nothing is playing at the time and there's
        # noise
        f0[f0 >= 0.9 * max_freq] = np.nan

        if np.isnan(f0).all():
            return np.nan, 0
        else:
            freq = float(np.nanmedian(f0))
            is_outlier = np.isnan(f0) | (np.abs(f0 - freq) > 0.3 * freq)
            confidence = 1 - is_outlier.mean()

            # Heuristic - if there are multiple outliers, the reading is noisy
            if is_outlier.sum() > 1:
                return np.nan, confidence
            else:
                return freq, confidence
