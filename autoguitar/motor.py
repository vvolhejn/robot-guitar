from abc import ABC
from queue import Queue
import threading
import time
import logging

logger = logging.getLogger(__name__)


class Motor(ABC):
    def step(self, forward: bool): ...


class VirtualMotor(Motor):
    def __init__(self, step_time_sec: float = 0.01):
        self.step_time_sec = step_time_sec
        self.total_steps_taken = 0

    def step(self, forward: bool):
        logger.debug(f"Stepping {'forward' if forward else 'backward'}")
        time.sleep(self.step_time_sec)
        self.total_steps_taken += 1


class MotorController:
    def __init__(self, motor: Motor, max_steps: int):
        self.motor = motor
        self.max_steps = max_steps

        self.cur_steps = 0
        self.target_steps = 0

        self.command_thread = None
        self.stop_thread = False

    def move(self, steps: int):
        self.target_steps += steps
        if self.target_steps > self.max_steps:
            self.target_steps = self.max_steps
        if self.target_steps < -self.max_steps:
            self.target_steps = -self.max_steps

    def __enter__(self):
        self.command_thread = threading.Thread(target=self._process_commands)
        self.command_thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_thread = True
        self.command_thread.join()

    def _process_commands(self):
        while not self.stop_thread:
            if self.cur_steps == self.target_steps:
                time.sleep(0.01)
                continue
            if self.cur_steps < self.target_steps:
                self.motor.step(forward=True)
                self.cur_steps += 1
            else:
                self.motor.step(forward=False)
                self.cur_steps -= 1
