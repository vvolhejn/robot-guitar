from typing import Annotated

import numpy as np
from pydantic import BaseModel, PlainValidator

from autoguitar.motor import AllMotorsStatus
from autoguitar.time_sync import UnixTimestamp


def none_to_nan(v: float | None) -> float:
    if v is None:
        return np.nan
    return float(v)


class TunerEvent(BaseModel):
    frequency: Annotated[float, PlainValidator(none_to_nan)]
    network_timestamp: UnixTimestamp


Event = TunerEvent | AllMotorsStatus

kind_to_event = {
    "tuner": TunerEvent,
    "all_motors_status": AllMotorsStatus,
}


def parse_event(data: object) -> Event:
    """Parse JSON data into an event, or raise if invalid."""
    if not isinstance(data, dict):
        raise ValueError("Event data must be a dictionary")

    kind = data["kind"]
    event_cls = kind_to_event[kind]
    return event_cls(**data["value"])
