import time

from autoguitar.dsp.audio_recorder import AudioRecorder
from autoguitar.dsp.input_stream import InputStream


def main():
    with InputStream(block_size=512) as input_stream:
        with AudioRecorder(path="output.wav", input_stream=input_stream):
            time.sleep(5)


if __name__ == "__main__":
    main()
