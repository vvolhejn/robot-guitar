from pydantic import BaseModel


class MidiEvent(BaseModel):
    pass  # TODO


class TunerEvent(BaseModel):
    frequency: float  # may be NaN
    target_frequency: float
    target_steps: int
    cur_steps: int


Event = MidiEvent | TunerEvent

kind_to_event = {
    "midi": MidiEvent,
    "tuner": TunerEvent,
}


def parse_event(data: object) -> Event:
    """Parse JSON data into an event, or raise if invalid."""
    if not isinstance(data, dict):
        raise ValueError("Event data must be a dictionary")

    kind = data["kind"]
    event_cls = kind_to_event[kind]
    return event_cls(**data["value"])
