# receiver.py
import mido

from autoguitar.motor import MotorController, get_motor
from autoguitar.pitch_detector import PitchDetector
from autoguitar.tuner import Tuner


def midi_note_to_frequency(midi_note: int):
    return 440.0 * (2 ** ((midi_note - 69) / 12.0))


def main():
    # Open the virtual input port connected to the sender.
    inport = mido.open_input("Launchkey Mini:Launchkey Mini LK Mini MIDI 28:0")

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
                    frequency = midi_note_to_frequency(msg.note)

                    while frequency > 140:
                        frequency /= 2
                    while frequency < 70:
                        frequency *= 2

                    tuner.target_frequency = frequency


if __name__ == "__main__":
    main()
