import datetime
from pathlib import Path

from pydantic import BaseModel

from autoguitar.dashboard.event import Event, UnixTimestamp
from autoguitar.time_sync import get_network_datetime

LOG_DIR = Path(__file__).parents[2] / "data" / "tuning_data"


class AnnotatedEvent(BaseModel):
    added_at_network_timestamp: UnixTimestamp
    event: Event


class EventStorage:
    def __init__(self):
        self.events = []
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        filename = get_network_datetime().strftime("%Y-%m-%d_%H-%M-%S") + ".jsonl"
        self.log_file_path = LOG_DIR / filename

    def add_event(self, event: Event):
        annotated_event = AnnotatedEvent(
            added_at_network_timestamp=get_network_datetime(), event=event
        )
        self.events.append(annotated_event)
        # append to logfile
        with open(self.log_file_path, "a") as f:
            f.write(annotated_event.model_dump_json() + "\n")

    def get_events(self):
        return self.events


EVENT_STORAGE = EventStorage()
