import logging
import random
import time

import click
import librosa
import numpy as np
import readchar
import requests

from autoguitar.dashboard.dash_app import PORT
from autoguitar.dsp.input_stream import InputStream
from autoguitar.dsp.pitch_detector import PitchDetector
from autoguitar.motor import MotorController, RemoteMotor, get_motor
from autoguitar.time_sync import get_network_timestamp

logger = logging.getLogger(__name__)


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
    print(f"Frequency: {frequency:.2f} Hz")
    event_data = {
        "frequency": frequency if not np.isnan(frequency) else None,
        "network_timestamp": get_network_timestamp(),
    }

    post_event(kind="tuner", value=event_data)


def main(pitch_detector: PitchDetector, mc0: MotorController, mc1: MotorController):
    pitch_detector.on_reading.subscribe(on_pitch_reading)

    tuner_motor = mc0.motor
    assert isinstance(tuner_motor, RemoteMotor), "Expected RemoteMotor"

    print(tuner_motor.get_all_motors_status())

    while True:
        mc0.set_target_steps(random.randint(-300, 300))
        for i in range(10):
            motors_status = tuner_motor.get_all_motors_status()
            post_event(
                kind="all_motors_status",
                value=motors_status.model_dump(mode="json"),
            )

            time.sleep(0.1)

        time.sleep(0.3)


@click.command()
def collect_tuning_data_cli():
    with InputStream(block_size=512) as input_stream:
        pitch_detector = PitchDetector(input_stream=input_stream)

        n_steps = [100, 25]

        motors = [get_motor(motor_number=0), get_motor(motor_number=1)]
        with (
            MotorController(motor=motors[0], max_steps=n_steps[0] * 100) as mc0,
            MotorController(motor=motors[1], max_steps=n_steps[1] * 100) as mc1,
        ):
            main(pitch_detector, mc0, mc1)


if __name__ == "__main__":
    collect_tuning_data_cli()
