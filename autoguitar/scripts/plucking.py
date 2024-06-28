import time

import numpy as np

from autoguitar.loudness_detector import LoudnessDetector
from autoguitar.motor import MotorController, get_motor


def find_pluck_position(
    mc: MotorController, ld: LoudnessDetector, loudness_difference: float, steps: int
):
    def get_loudness():
        ld.readings.clear()
        while len(ld.readings) < 2:
            time.sleep(0.001)
        return ld.get_mean_loudness()

    last_loudness = get_loudness()

    while True:
        mc.move(steps, wait=True)
        loudness2 = get_loudness()
        loudness1 = last_loudness

        normalized_difference = (loudness2 - loudness1) / loudness_difference
        # print(f"{loudness1:.4f} {loudness2:.4f} {normalized_difference:.4f}")
        last_loudness = loudness2

        if normalized_difference > 0.1:
            # print("Plucked!")
            break

    return mc.get_target_steps()


def main():
    steps_per_turn = 1600

    motor = get_motor(motor_number=1)

    with MotorController(motor=motor, max_steps=int(1e9)) as mc:
        # Randomize the motor position for testing purposes
        mc.move(np.random.randint(-steps_per_turn, steps_per_turn))

        with LoudnessDetector() as ld:
            print("Waiting for loudness detector to initialize", end="", flush=True)
            while not ld.readings:
                time.sleep(1)
                print(".", end="", flush=True)
            print()

            # Before finding the plucking position, measure loudness when nothing
            # is playing vs when the string is plucked.
            silence_loudness = ld.get_mean_loudness()
            ld.readings.clear()
            mc.move(steps_per_turn * 2, wait=True)
            plucking_loudness = ld.get_mean_loudness()

            print(f"Silence loudness: {silence_loudness:.4f} units")
            print(f"Plucking loudness: {plucking_loudness:.4f} units")
            loudness_difference = plucking_loudness - silence_loudness

            # Moving by small steps is slow, so first take big steps to roughly
            # find where the string is
            time.sleep(0.5)
            find_pluck_position(
                mc, ld, loudness_difference=loudness_difference, steps=-100
            )
            mc.move(-100, wait=True)
            time.sleep(0.5)

            # Now move in small steps until the string is plucked
            position_up = find_pluck_position(
                mc, ld, loudness_difference=loudness_difference, steps=5
            )
            print("Upstroke position:", position_up)
            time.sleep(1)
            position_down = find_pluck_position(
                mc, ld, loudness_difference=loudness_difference, steps=-5
            )
            print("Downstroke position:", position_down)

            # Try playing a strumming pattern
            time.sleep(1)
            sleep = 0.07
            for _ in range(10):
                mc.set_target_steps(position_up, wait=True)  # strum up
                time.sleep(sleep)
                mc.set_target_steps(position_down + 10, wait=True)  # mute
                time.sleep(sleep * 2)
                mc.set_target_steps(position_down - 10, wait=True)  # strum down
                time.sleep(sleep)
                mc.set_target_steps(position_down + 15, wait=True)  # mute
                time.sleep(sleep * 2)


if __name__ == "__main__":
    main()
