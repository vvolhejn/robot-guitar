from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import FastAPI, Request
from pydantic import BaseModel, BeforeValidator

from autoguitar.motor import MotorController, get_motor


@asynccontextmanager
async def lifespan(app: FastAPI):
    motors = [get_motor(motor_number=0), get_motor(motor_number=1)]

    with (
        MotorController(motor=motors[0], max_steps=3000) as mc0,
        MotorController(motor=motors[1], max_steps=3000) as mc1,
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
    target_steps: int


@app.post("/motor_turn")
def post_motor_turn(request: Request, motor_turn: MotorTurn):
    mc = get_motor_controllers_from_request(request)[motor_turn.motor_number]
    mc.set_target_steps(motor_turn.target_steps)
    return motor_turn.model_dump()


@app.get("/motors_status")
def get_motors_status(request: Request):
    mcs = get_motor_controllers_from_request(request)
    return {i: {"cur_steps": mc.cur_steps} for i, mc in enumerate(mcs)}
