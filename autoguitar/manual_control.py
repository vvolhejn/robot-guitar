import time

import readchar

from autoguitar.motor import MotorController, get_motor


def manual_control():
    print("Press arrow keys or q to exit")

    motor = get_motor()
    with MotorController(motor=motor, max_steps=1000) as mc:
        while True:
            print("Current rotation: ", mc.cur_steps)

            key = readchar.readkey()

            if mc.is_moving():
                print("Still moving, skipping...")
                continue

            if key.lower() == "d":
                print("You pressed Wind less!")
                mc.move(-100)
                time.sleep(0.001)
            elif key.lower() == "f":
                print("You pressed Wind more!")
                mc.move(100)
                time.sleep(0.001)
            elif key == "q":
                print("Exiting...")
                break


if __name__ == "__main__":
    manual_control()
