import logging

import click
import librosa
import mido
import numpy as np

from autoguitar.control.strummer import Strummer
from autoguitar.dsp.input_stream import InputStream
from autoguitar.midi_utils import find_midi_input
from autoguitar.motor import MotorController, get_motor
from autoguitar.tuner import Tuner

logging.basicConfig(level=logging.INFO)


@click.command()
@click.option("--strummer/--no-strummer", "use_strummer", default=True)
def main(use_strummer: bool):
    # Open the virtual input port connected to the sender.
    midi_input_name = find_midi_input()
    inport = mido.open_input(midi_input_name)
    print("Using MIDI input:", midi_input_name)

    motors = [get_motor(motor_number=0), get_motor(motor_number=1)]

    with (
        InputStream(block_size=512) as input_stream,
        MotorController(motor=motors[0], max_steps=10000) as mc0,
        MotorController(motor=motors[1], max_steps=10000) as mc1,
    ):
        # Randomize the motor position for testing purposes
        mc1.move(
            np.random.randint(-mc1.steps_per_turn(), mc1.steps_per_turn()), wait=True
        )

        if use_strummer:
            strummer = Strummer(input_stream=input_stream, motor_controller=mc1)
            strummer.calibrate()
        else:
            strummer = None

        # Create the tuner only after the strummer has been calibrated
        # so that it doesn't move the string while we're calibrating
        tuner = Tuner(
            input_stream=input_stream,
            motor_controller=mc0,
            initial_target_frequency=float(librosa.note_to_hz("C3")),
        )

        for msg in inport:
            print(msg)
            if msg.type == "note_on":
                frequency = librosa.midi_to_hz(msg.note)

                while frequency > librosa.note_to_hz("G3") + 1e-3:
                    frequency /= 2
                while frequency < librosa.note_to_hz("G1") - 1e-3:
                    frequency *= 2

                tuner.target_frequency = frequency

                if strummer is not None:
                    strummer.strum()

                if readings := tuner.pitch_detector.frequency_readings:
                    # Fake reading to let the tuner know the target frequency has changed
                    tuner.on_pitch_reading(readings[-1])
            elif msg.type == "note_off":
                pass
                # TODO: mute. The muting is a bit too unreliable atm.
                # if strummer is not None:
                #     strummer.mute()


if __name__ == "__main__":
    main()
