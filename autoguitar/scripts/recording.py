import time

from autoguitar.dsp.audio_recorder import AudioRecorder
from autoguitar.dsp.input_stream import InputStream
from autoguitar.dsp.pitch_detector import PitchDetector


def main():
    with InputStream(block_size=512) as input_stream:
        # Run the pitch detector at the same time to check if some blocks get
        # dropped due to input overflow (since pitch detection is
        # computationally expensive)
        pitch_detector = PitchDetector(input_stream=input_stream)

        def on_pitch_reading(data: tuple[float, float]):
            frequency, _timestamp = data
            print(f"Frequency: {frequency:.2f} Hz")

        pitch_detector.on_reading.subscribe(on_pitch_reading)
        time.sleep(1)
        input_stream.wait_for_initialization()

        with AudioRecorder(path="output.wav", input_stream=input_stream):
            time.sleep(10)


if __name__ == "__main__":
    main()
