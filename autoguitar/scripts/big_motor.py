"""Playing around with a bigger steper motor."""

import random
import time

import RPi.GPIO as GPIO

from autoguitar.motor import PIN_CONFIGURATIONS


def main():
    GPIO.setmode(GPIO.BOARD)
    # 18, 3, 12
    step_pin = 22
    direction_pin = 5
    disable_pin = 13

    GPIO.setup(step_pin, GPIO.OUT)
    GPIO.setup(direction_pin, GPIO.OUT)
    GPIO.setup(disable_pin, GPIO.OUT)

    GPIO.output(step_pin, 0)
    GPIO.output(disable_pin, 0)
    GPIO.output(direction_pin, 0)

    step_time_sec = 0.01

    def step(forward: bool):
        GPIO.output(direction_pin, forward)
        GPIO.output(step_pin, 1)
        time.sleep(step_time_sec / 2)
        GPIO.output(step_pin, 0)
        time.sleep(step_time_sec / 2)

    print("stepping")
    try:
        # while True:
        #     # pin = random.choice([step_pin, direction_pin, disable_pin])
        #     pin = random.choice([step_pin, disable_pin])
        #     output = random.choice([False, True])
        #     GPIO.output(pin, output)
        #     time.sleep(step_time_sec)

        while True:
            for _ in range(100):
                step(forward=False)
            for _ in range(50):
                step(forward=True)
            print(".", end="", flush=True)
    except KeyboardInterrupt:
        GPIO.cleanup()
        raise

    # print("waiting")
    # while True:
    #     time.sleep(1)


if __name__ == "__main__":
    main()
