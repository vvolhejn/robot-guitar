import itertools
import logging
import random
import time

import click
import librosa
import numpy as np
import requests

from autoguitar.dashboard.dash_app import PORT
from autoguitar.dsp.input_stream import InputStream
from autoguitar.motor import MotorController, RemoteMotor, get_motor
from autoguitar.time_sync import get_network_timestamp
from autoguitar.tuning.tuner import Tuner
from autoguitar.tuning.tuner_strategy import (
    ModelBasedTunerStrategy,
    ProportionalTunerStrategy,
)

logger = logging.getLogger(__name__)

BPM = 147
BEATS_PER_BAR = 8
TIMEOUT = 60 / BPM * BEATS_PER_BAR
NOTES = ["D#2", "C2", "F2", "A#1"]
MEASUREMENT_SUBDIVISION = 16


def post_event(kind: str, value: dict):
    try:
        response = requests.post(
            f"http://localhost:{PORT}/api/event",
            json={"kind": kind, "value": value},
            timeout=2,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Failed to post event: {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to post event: {e}")


def on_pitch_reading(data: tuple[float, float]):
    frequency, _timestamp = data
    event_data = {
        "frequency": frequency if not np.isnan(frequency) else None,
        "network_timestamp": get_network_timestamp(),
    }

    post_event(kind="tuner", value=event_data)


def main(
    input_stream: InputStream,
    mc0: MotorController,
    mc1: MotorController,
    random_notes: bool,
):
    # tuner_strategy = ProportionalTunerStrategy(max_n_steps=1000, speed=10.0)
    tuner_strategy = ModelBasedTunerStrategy(
        coef=3.5,  # 4.35
        adaptiveness=0.5,
    )
    tuner = Tuner(
        input_stream=input_stream,
        motor_controller=mc0,
        initial_target_frequency=65,
        tuner_strategy=tuner_strategy,
    )

    tuner.pitch_detector.on_reading.subscribe(on_pitch_reading)

    tuner_motor = mc0.motor
    assert isinstance(tuner_motor, RemoteMotor), "Expected RemoteMotor"

    for note in itertools.cycle(NOTES):
        if random_notes:
            tuner.target_frequency = random.uniform(60, 100)
        else:
            tuner.target_frequency = float(librosa.note_to_hz(note))

        for _ in range(MEASUREMENT_SUBDIVISION):
            motors_status = tuner_motor.get_all_motors_status()
            post_event(
                kind="all_motors_status",
                value=motors_status.model_dump(mode="json"),
            )

            time.sleep(TIMEOUT / MEASUREMENT_SUBDIVISION)


@click.command()
@click.option("--random-notes/--no-random-notes", default=True)
def collect_tuning_data_cli(random_notes: bool):
    with InputStream(block_size=512) as input_stream:
        n_steps = [100, 25]

        motors = [get_motor(motor_number=0), get_motor(motor_number=1)]
        with (
            MotorController(motor=motors[0], max_steps=n_steps[0] * 100) as mc0,
            MotorController(motor=motors[1], max_steps=n_steps[1] * 100) as mc1,
        ):
            main(input_stream, mc0, mc1, random_notes=random_notes)


if __name__ == "__main__":
    collect_tuning_data_cli()
