import logging
import time
from threading import Thread

import click
import librosa
import mido
import numpy as np

from autoguitar.control.strummer import Strummer
from autoguitar.dsp.input_stream import InputStream
from autoguitar.midi_utils import find_midi_input
from autoguitar.motor import RemoteMotorController
from autoguitar.tuning.tuner import Tuner

logging.basicConfig(level=logging.INFO)


MIN_FREQUENCY = librosa.note_to_hz("E1")
MAX_FREQUENCY = librosa.note_to_hz("G#2")
INITIAL_TARGET_FREQUENCY = librosa.note_to_hz("E2")


def remap(
    x: float, in_min: float, in_max: float, out_min: float, out_max: float
) -> float:
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


@click.command()
@click.option("--strummer/--no-strummer", "use_strummer", default=True)
@click.option("--midi-keyboard/--no-midi-keyboard", "use_midi_keyboard", default=True)
def main(use_strummer: bool, use_midi_keyboard: bool):
    if use_midi_keyboard:
        # Open the virtual input port connected to the sender.
        midi_input_name = find_midi_input()
        inport = mido.open_input(midi_input_name)
        print("Using MIDI input:", midi_input_name)
    else:
        port_name = "Autoguitar"
        inport = mido.open_input(port_name, virtual=True)
        print("Opened virtual MIDI port:", port_name)

    # motors = [get_motor(motor_number=0), get_motor(motor_number=1)]

    with (
        InputStream(block_size=512) as input_stream,
        RemoteMotorController(motor_number=0) as mc0,
        RemoteMotorController(motor_number=1) as mc1,
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
            initial_target_frequency=float(INITIAL_TARGET_FREQUENCY),
        )

        tremolo_frequency: float | None = None

        def tremolo_loop():
            while True:
                freq = tremolo_frequency
                if freq is not None:
                    assert 0.1 < freq <= 100

                    strum_start = time.time()
                    if strummer is not None:
                        strummer.strum()
                    strum_end = time.time()

                    time.sleep(max(0, 1 / freq - (strum_end - strum_start)))
                else:
                    time.sleep(0.1)

        tremolo_thread = Thread(target=tremolo_loop)
        tremolo_thread.start()

        for msg in inport:
            if msg.type == "note_on":
                print(msg)
                frequency = librosa.midi_to_hz(msg.note)

                while frequency > MAX_FREQUENCY + 1e-3:
                    frequency /= 2
                while frequency < MIN_FREQUENCY - 1e-3:
                    frequency *= 2

                tuner.target_frequency = frequency

                if strummer is not None and tremolo_frequency is None:
                    strummer.strum()

                if readings := tuner.pitch_detector.frequency_readings:
                    # Fake reading to let the tuner know the target frequency has changed
                    tuner.on_pitch_reading(readings[-1])
            elif msg.type == "note_off":
                pass
                # TODO: mute. The muting is a bit too unreliable atm.
                # if strummer is not None:
                #     strummer.mute()
            elif msg.type == "control_change":
                if (
                    msg.control in [21, 22]  # knobs 1 and 2 on the Launchkey Mini
                    and strummer
                ):
                    max_offset = 25
                    offset = round(remap(msg.value, 0, 127, -max_offset, max_offset))
                    if msg.control == 21:
                        strummer.downstroke_offset = offset
                    else:
                        strummer.upstroke_offset = offset
                    pass
                elif (
                    msg.control == 23
                    and msg.value in [0, 127]
                    and strummer
                    and strummer.calibration
                ):
                    sign = +1 if msg.value > 64 else -1
                    strummer.calibration.downstroke_steps += 10 * sign
                    strummer.calibration.upstroke_steps += 10 * sign

                elif msg.control == 24 and msg.value in [0, 127]:
                    mc0.move(1000 if msg.value > 64 else -1000, wait=True)

                elif msg.control == 28:  # knob 8 on the Launchkey Mini
                    # Tremolo
                    if msg.value < 64:
                        tremolo_frequency = None
                    else:
                        tremolo_exponent = remap(msg.value, 64, 127, 0, 1)
                        min_freq = 1
                        max_freq = 50
                        tremolo_frequency = (
                            min_freq * (max_freq / min_freq) ** tremolo_exponent
                        )

        tremolo_thread.join()


if __name__ == "__main__":
    main()
