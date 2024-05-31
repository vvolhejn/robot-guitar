import datetime

from pydantic import BaseModel

from autoguitar.dashboard.event import Event


class AnnotatedEvent(BaseModel):
    datetime: datetime.datetime
    event: Event


class EventStorage:
    def __init__(self):
        self.events = []

    def add_event(self, event: Event):
        annotated_event = AnnotatedEvent(datetime=datetime.datetime.now(), event=event)
        self.events.append(annotated_event)

    def get_events(self):
        return self.events


EVENT_STORAGE = EventStorage()
