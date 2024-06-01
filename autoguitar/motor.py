import logging
import threading
import time
from abc import ABC
from types import TracebackType
from typing import Optional

from autoguitar.virtual_string import VirtualString

logger = logging.getLogger(__name__)


class Motor(ABC):
    def step(self, forward: bool): ...


class PhysicalMotor(Motor):
    def __init__(self, flip_direction: bool, sleep_time_sec: float = 0.0001):
        self.flip_direction = flip_direction
        self.sleep_time_sec = sleep_time_sec

        import RPi.GPIO as GPIO

        GPIO.setmode(GPIO.BOARD)
        self.step_pin = 11
        self.direction_pin = 15
        self.disable_pin = 19  # a "0" signal enables the motor

        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.direction_pin, GPIO.OUT)
        GPIO.setup(self.disable_pin, GPIO.OUT)
        GPIO.output(self.disable_pin, 0)
        GPIO.output(self.direction_pin, 1)

    def step(self, forward: bool):
        logger.debug(f"Stepping {'forward' if forward else 'backward'}")
        import RPi.GPIO as GPIO

        GPIO.output(self.direction_pin, forward != self.flip_direction)
        GPIO.output(self.step_pin, 1)
        time.sleep(self.sleep_time_sec)
        GPIO.output(self.step_pin, 0)
        time.sleep(self.sleep_time_sec)


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

    def set_target_steps(self, steps: int):
        self._target_steps = steps
        if self._target_steps > self.max_steps:
            self._target_steps = self.max_steps
        if self._target_steps < -self.max_steps:
            self._target_steps = -self.max_steps

    def get_target_steps(self) -> int:
        return self._target_steps

    def move(self, steps: int):
        self.set_target_steps(self._target_steps + steps)

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


def is_raspberry_pi():
    try:
        with open("/proc/cpuinfo", "r") as f:
            return "Raspberry" in f.read()
    except FileNotFoundError:
        return False


def get_motor():
    if is_raspberry_pi():
        logger.info("Using physical motor.")
        return PhysicalMotor(flip_direction=True)
    else:
        logger.info("Using virtual motor.")
        return VirtualMotor(step_time_sec=0.1)
