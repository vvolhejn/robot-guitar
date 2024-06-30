import threading
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class Signal(Generic[T]):
    def __init__(self):
        self._observers = set()
        self._lock = threading.Lock()

    def subscribe(self, callback: Callable[[T], None]):
        """Registers a callback to the event."""
        with self._lock:
            self._observers.add(callback)

    def unsubscribe(self, callback: Callable[[T], None]):
        """Unregisters a callback from the event."""
        with self._lock:
            try:
                self._observers.remove(callback)
            except ValueError:
                print(
                    "Warning: Tried to unsubscribe a callback that was not subscribed."
                )

    def notify(self, value: T):
        """Notifies all registered observers about an event."""
        # Avoid holding the lock while calling the observers
        with self._lock:
            observers_snapshot = list(self._observers)

        for observer in observers_snapshot:
            observer(value)
