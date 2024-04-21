import time

from autoguitar.motor import MotorController, VirtualMotor


def test_motor_controller_basic():
    with MotorController(motor=VirtualMotor(step_time_sec=0.001), max_steps=100) as mc:
        mc.move(10)
        time.sleep(0.1)

    assert mc.cur_steps == 10


def test_motor_controller_no_sleep():
    with MotorController(motor=VirtualMotor(step_time_sec=0.001), max_steps=1000) as mc:
        mc.move(1000)

    # We didn't sleep at all, so the thread should terminate before it gets
    # to the target steps.
    assert mc.cur_steps < 1000


def test_motor_controller_max_steps():
    step_time_sec = 0.001
    motor = VirtualMotor(step_time_sec=step_time_sec)

    with MotorController(motor=motor, max_steps=10) as mc:
        mc.move(15)
        time.sleep(0.1)
    assert mc.cur_steps == 10

    with MotorController(motor=motor, max_steps=10) as mc:
        mc.move(-15)
        time.sleep(0.1)
    assert mc.cur_steps == -10


def test_motor_controller_step_tracking():
    with MotorController(motor=VirtualMotor(step_time_sec=0.001), max_steps=5) as mc:
        mc.move(4)
        mc.move(3)  # we cap at 5
        mc.move(-7)
        time.sleep(0.1)
        assert mc.cur_steps == -2
        mc.move(-100)
        time.sleep(0.1)
        assert mc.cur_steps == -5


def test_motor_controller_saving_steps():
    motor = VirtualMotor(step_time_sec=0.001)
    with MotorController(motor=motor, max_steps=1000) as mc:
        mc.move(40)
        mc.move(-20)
        time.sleep(0.1)
        # We don't move backwards and forwards because `target_steps` gets modified
        # before all of the steps are executed, so we only do one move.
        assert motor.total_steps_taken == 20
