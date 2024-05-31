from pydantic import BaseModel


class MidiEvent(BaseModel):
    pass  # TODO


class PitchReadingEvent(BaseModel):
    freq: float  # may be NaN


Event = MidiEvent | PitchReadingEvent

kind_to_event = {
    "midi": MidiEvent,
    "pitch_reading": PitchReadingEvent,
}


def parse_event(data: object) -> Event:
    """Parse JSON data into an event, or raise if invalid."""
    if not isinstance(data, dict):
        raise ValueError("Event data must be a dictionary")

    kind = data["kind"]
    event_cls = kind_to_event[kind]
    return event_cls(**data["value"])
