# receiver.py
import librosa
import mido

from autoguitar.motor import MotorController, get_motor
from autoguitar.pitch_detector import PitchDetector
from autoguitar.tuner import Tuner


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
                initial_target_frequency=70,
            )

            for msg in inport:
                print(msg)
                if msg.type == "note_on":
                    frequency = librosa.midi_to_hz(msg.note)

                    while frequency > 140:
                        frequency /= 2
                    while frequency < 70:
                        frequency *= 2

                    tuner.target_frequency = frequency


if __name__ == "__main__":
    main()
