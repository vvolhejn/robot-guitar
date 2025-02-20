import logging
import time
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, BeforeValidator

from autoguitar.motor import AllMotorsStatus, MotorController, MotorStatus, get_motor
from autoguitar.time_sync import get_network_datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    motors = [
        get_motor(motor_number=0),
        get_motor(motor_number=1),
    ]

    with (
        MotorController(motor=motors[0], max_steps=100000) as mc0,
        MotorController(motor=motors[1], max_steps=100000) as mc1,
    ):
        yield {"mc0": mc0, "mc1": mc1}


def get_motor_controllers_from_request(
    request: Request,
) -> tuple[MotorController, MotorController]:
    return request.state.mc0, request.state.mc1


app = FastAPI(lifespan=lifespan)


class MotorTurn(BaseModel):
    # BeforeValidator is needed because FastAPI doesn't convert from string to int
    # automatically when you use `Literal`
    motor_number: Annotated[Literal[0, 1], BeforeValidator(int)]
    steps: int
    relative: bool = False


@app.post("/motor_turn")
def post_motor_turn(request: Request, motor_turn: MotorTurn):
    mc = get_motor_controllers_from_request(request)[motor_turn.motor_number]

    # if mc.is_moving():
    #     if motor_turn.motor_number == 1:
    #         print("SKIP", motor_turn)

    #     # To avoid race condition
    #     return motor_turn.model_copy(
    #         update={"steps": 0 if motor_turn.relative else mc.cur_steps}
    #     ).model_dump()

    if mc.is_moving():
        # To avoid race condition
        raise HTTPException(status_code=400, detail="Motor is currently moving")

    t1 = time.time()

    if motor_turn.motor_number == 1:
        print("START", motor_turn)

    # It's important to wait here because otherwise the motor controller will think that
    # it has already completed the move when in fact it hasn't. This is especially
    # important for tuner calculations because they look at the relationship between
    # motor position and frequency.
    if motor_turn.relative:
        mc.move(motor_turn.steps, wait=True)
    else:
        mc.set_target_steps(motor_turn.steps, wait=True)

    t2 = time.time()
    if motor_turn.motor_number == 1:
        print(f"DONE {(t2 - t1):.3f}", motor_turn)

    return motor_turn.model_dump()


@app.get("/all_motors_status")
def get_all_motors_status(request: Request):
    mcs = get_motor_controllers_from_request(request)
    return AllMotorsStatus(
        network_timestamp=get_network_datetime(),
        status=[
            MotorStatus(
                motor_number=i,
                cur_steps=mc.cur_steps,
                target_steps=mc.get_target_steps(),
            )
            for i, mc in enumerate(mcs)
        ],
    ).model_dump()


@app.get("/health")
def health():
    """Check if the server is running."""
    return {"status": "ok"}


@app.get("/reset")
def reset(request: Request):
    # If we use the server over multiple runs, we want to reset the motor positions
    # to 0. Otherwise the first command might make a really big move if the motor
    # is already at a very high/low position.
    mc0, mc1 = get_motor_controllers_from_request(request)
    for mc in [mc0, mc1]:
        mc.cur_steps = 0
        mc.set_target_steps(0)
