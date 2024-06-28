import logging
import threading
import time
from abc import ABC
from dataclasses import dataclass
from types import TracebackType
from typing import Optional

from autoguitar.virtual_string import VirtualString

logger = logging.getLogger(__name__)

STEPS_PER_TURN = 1600


class Motor(ABC):
    def step(self, forward: bool): ...


@dataclass  # Use Pydantic?
class PinConfiguration:
    step: int
    direction: int
    disable: int  # a "0" signal enables the motor


PIN_CONFIGURATIONS = [
    PinConfiguration(step=11, direction=15, disable=19),
    PinConfiguration(step=18, direction=16, disable=12),
]


class PhysicalMotor(Motor):
    def __init__(
        self, motor_number: int, flip_direction: bool, step_time_sec: float = 0.0002
    ):
        self.flip_direction = flip_direction
        self.step_time_sec = step_time_sec

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
        logger.debug(f"Stepping {'forward' if forward else 'backward'}")
        import RPi.GPIO as GPIO

        GPIO.output(self.direction_pin, forward != self.flip_direction)
        GPIO.output(self.step_pin, 1)
        time.sleep(self.step_time_sec / 2)
        GPIO.output(self.step_pin, 0)
        time.sleep(self.step_time_sec / 2)


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
        logger.debug(f"Stepping {'forward' if forward else 'backward'}")
        time.sleep(self.step_time_sec)
        self.total_steps_taken += 1

        if self.virtual_string:
            self.virtual_string.shift_frequency(10 if forward else -10)


class MotorController:
    def __init__(self, motor: Motor, max_steps: int):
        self.motor = motor
        self.max_steps = max_steps

        self.cur_steps = 0
        self._target_steps = 0

        self.command_thread = None
        self.stop_thread = False

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
        self.stop_thread = True
        assert self.command_thread is not None
        self.command_thread.join()

    def _process_commands(self):
        while not self.stop_thread:
            if self.cur_steps == self._target_steps:
                time.sleep(0.001)
                continue
            if self.cur_steps < self._target_steps:
                self.motor.step(forward=True)
                self.cur_steps += 1
            else:
                self.motor.step(forward=False)
                self.cur_steps -= 1

    def wait_until_stopped(self):
        while self.is_moving():
            time.sleep(0.01)


def is_raspberry_pi():
    try:
        with open("/proc/cpuinfo", "r") as f:
            return "Raspberry" in f.read()
    except FileNotFoundError:
        return False


def get_motor(motor_number: int = 0):
    if is_raspberry_pi():
        logger.info(f"Using physical motor {motor_number=}.")
        return PhysicalMotor(motor_number=motor_number, flip_direction=False)
    else:
        logger.info("Using virtual motor.")
        return VirtualMotor(step_time_sec=0.1)
