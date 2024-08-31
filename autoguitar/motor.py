import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import TracebackType
from typing import Optional

import requests

from autoguitar.virtual_string import VirtualString

logger = logging.getLogger(__name__)

STEP_TIME_SEC_PER_MOTOR = [0.0002, 0.0004]
# Microstepping is a feature of stepper motors that allows them to move in
# smaller increments than a full step. This can be used to increase the
# resolution of the motor, but it also reduces the torque. The values below
# are the number of microsteps per full step.
MICROSTEPPING_PER_MOTOR = [8, 2]
STEPS_PER_TURN_WITHOUT_MICROSTEPPING = 200


class Motor(ABC):
    @abstractmethod
    def step(self, forward: bool): ...

    @abstractmethod
    def steps_per_turn(self) -> int: ...

    def step_multiple(self, n: int):
        """Can be overridden for more efficient implementations."""
        if n == 0:
            return
        forward = True if n > 0 else False

        for _ in range(abs(n)):
            self.step(forward)


@dataclass  # Use Pydantic?
class PinConfiguration:
    step: int
    direction: int
    disable: int  # a "0" signal enables the motor


PIN_CONFIGURATIONS = [
    PinConfiguration(step=11, direction=16, disable=19),
    PinConfiguration(step=18, direction=15, disable=12),
]


class PhysicalMotor(Motor):
    def __init__(
        self,
        motor_number: int,
        flip_direction: bool,
        step_time_sec: float,
        microstepping: int,
    ):
        self.flip_direction = flip_direction
        self.step_time_sec = step_time_sec
        self.microstepping = microstepping

        import RPi.GPIO as GPIO

        GPIO.setmode(GPIO.BOARD)
        pin_configuration = PIN_CONFIGURATIONS[motor_number]
        self.step_pin = pin_configuration.step
        self.direction_pin = pin_configuration.direction
        self.disable_pin = pin_configuration.disable

        # Ignore "This channel is already in use, continuing anyway."
        # We intentionally don't release the channels when the program is quit
        # because it leaves the values in floating states, which sometimes
        # leads to the motors moving even when nothing is running.
        GPIO.setwarnings(False)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.direction_pin, GPIO.OUT)
        GPIO.setup(self.disable_pin, GPIO.OUT)
        GPIO.setwarnings(True)

        GPIO.output(self.disable_pin, 0)
        GPIO.output(self.direction_pin, 1)

    def step(self, forward: bool):
        import RPi.GPIO as GPIO

        GPIO.output(self.direction_pin, forward != self.flip_direction)
        GPIO.output(self.step_pin, 1)
        time.sleep(self.step_time_sec / 2)
        GPIO.output(self.step_pin, 0)
        time.sleep(self.step_time_sec / 2)

    def steps_per_turn(self) -> int:
        return STEPS_PER_TURN_WITHOUT_MICROSTEPPING * self.microstepping


class VirtualMotor(Motor):
    def __init__(
        self,
        step_time_sec: float = 0.01,
        virtual_string: Optional[VirtualString] = None,
    ):
        self.step_time_sec = step_time_sec
        self.total_steps_taken = 0
        self.virtual_string = virtual_string

    def step(self, forward: bool):
        time.sleep(self.step_time_sec)
        self.total_steps_taken += 1

        if self.virtual_string:
            self.virtual_string.shift_frequency(10 if forward else -10)

    def steps_per_turn(self) -> int:
        return STEPS_PER_TURN_WITHOUT_MICROSTEPPING


class RemoteMotor(Motor):
    def __init__(
        self,
        motor_number: int,
        step_time_sec: float,
        microstepping: int,
    ):
        self.motor_number = motor_number
        self.step_time_sec = step_time_sec
        self.microstepping = microstepping
        self.server_url = "http://localhost:8050"

        response = requests.get(f"{self.server_url}/health")
        if response.status_code != 200:
            raise RuntimeError(f"Motor server is not running: {response}")

    def step(self, forward: bool):
        raise NotImplementedError

    def step_multiple(self, n: int):
        response = requests.post(
            f"{self.server_url}/motor_turn",
            json={
                "motor_number": self.motor_number,
                "target_steps": n,
                "relative": True,
            },
        )
        response.raise_for_status()

    def steps_per_turn(self) -> int:
        return STEPS_PER_TURN_WITHOUT_MICROSTEPPING * self.microstepping


class MotorController:
    def __init__(self, motor: Motor, max_steps: int):
        self.motor = motor
        self.max_steps = max_steps

        self.cur_steps = 0
        self._target_steps = 0

        self.command_thread = None
        self.stop_event = threading.Event()

    def set_target_steps(self, steps: int, wait: bool = False):
        self._target_steps = steps
        if self._target_steps > self.max_steps:
            self._target_steps = self.max_steps
        if self._target_steps < -self.max_steps:
            self._target_steps = -self.max_steps

        if wait:
            self.wait_until_stopped()

    def get_target_steps(self) -> int:
        return self._target_steps

    def move(self, steps: int, wait: bool = False):
        self.set_target_steps(self._target_steps + steps, wait=wait)

    def is_moving(self) -> bool:
        return self.cur_steps != self._target_steps

    def __enter__(self):
        self.command_thread = threading.Thread(target=self._process_commands)
        self.command_thread.start()
        return self

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: TracebackType):
        self.stop_event.set()
        assert self.command_thread is not None
        self.command_thread.join()

    def _process_commands(self):
        while not self.stop_event.is_set():
            if self.cur_steps == self._target_steps:
                time.sleep(0.001)
                continue

            target_steps = self._target_steps
            self.motor.step_multiple(target_steps - self.cur_steps)
            self.cur_steps = target_steps

    def wait_until_stopped(self):
        while self.is_moving():
            time.sleep(0.01)

    def steps_per_turn(self) -> int:
        return self.motor.steps_per_turn()


def is_raspberry_pi():
    try:
        with open("/proc/cpuinfo", "r") as f:
            return "Raspberry" in f.read()
    except FileNotFoundError:
        return False


def get_motor(motor_number: int = 0, remote: bool = True) -> Motor:
    step_time_sec = STEP_TIME_SEC_PER_MOTOR[motor_number]
    if is_raspberry_pi():
        logger.debug(f"Using physical motor {motor_number=}.")
        return PhysicalMotor(
            motor_number=motor_number,
            flip_direction=False,
            step_time_sec=step_time_sec,
            microstepping=MICROSTEPPING_PER_MOTOR[motor_number],
        )
    elif remote:
        logger.debug("Using remote motor.")
        return RemoteMotor(
            motor_number=motor_number,
            step_time_sec=step_time_sec,
            microstepping=MICROSTEPPING_PER_MOTOR[motor_number],
        )
    else:
        logger.debug("Using virtual motor.")
        return VirtualMotor(step_time_sec=step_time_sec * 100)
