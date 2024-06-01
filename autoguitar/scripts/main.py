# receiver.py
import logging

import librosa
import mido

from autoguitar.motor import MotorController, get_motor
from autoguitar.pitch_detector import PitchDetector
from autoguitar.tuner import Tuner

logging.basicConfig(level=logging.INFO)


def find_midi_input() -> str:
    substring = "Launchkey Mini:Launchkey Mini LK Mini MIDI"
    for name in mido.get_input_names():
        if substring in name:
            return name

    raise OSError(
        f"Could not open MIDI input port matching {repr(substring)}. "
        f"Available ports: {mido.get_input_names()}"
    )


def main():
    # Open the virtual input port connected to the sender.
    midi_input_name = find_midi_input()
    inport = mido.open_input(midi_input_name)
    print("Using MIDI input:", midi_input_name)

    motor = get_motor()
    with PitchDetector() as pitch_detector:
        with MotorController(motor=motor, max_steps=10000) as mc:
            tuner = Tuner(
                pitch_detector=pitch_detector,
                motor_controller=mc,
                initial_target_frequency=float(librosa.note_to_hz("C3")),
            )

            for msg in inport:
                print(msg)
                if msg.type == "note_on":
                    frequency = librosa.midi_to_hz(msg.note)

                    frequency_orig = frequency

                    while frequency > librosa.note_to_hz("C4") + 1e-3:
                        frequency /= 2
                    while frequency < librosa.note_to_hz("C2") - 1e-3:
                        frequency *= 2

                    tuner.target_frequency = frequency

                    if pitch_detector.frequency_readings:
                        # Fake reading to let the tuner know the target frequency has changed
                        tuner.on_pitch_reading(pitch_detector.frequency_readings[-1])


if __name__ == "__main__":
    main()
