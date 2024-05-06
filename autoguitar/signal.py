import weakref
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class Signal(Generic[T]):
    def __init__(self):
        # a WeakSet allows the observer to be garbage collected if it's not used
        self._observers = weakref.WeakSet()

    def subscribe(self, callback: Callable[[T], None]):
        """Registers a callback to the event."""
        self._observers.add(callback)

    def unsubscribe(self, callback: Callable[[T], None]):
        """Unregisters a callback from the event."""
        try:
            self._observers.remove(callback)
        except ValueError:
            print("Warning: Tried to unsubscribe a callback that was not subscribed.")

    def notify(self, value: T):
        """Notifies all registered observers about an event."""
        for observer in self._observers:
            observer(value)
