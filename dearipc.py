from multiprocessing import Manager, Process, Queue, sleep


class PubSub:
    _manager = None
    _state = None
    _subscribers = {}

    @classmethod
    def initialized(cls):
        return cls._state is not None

    @classmethod
    def get_state(cls):
        if cls._state is None:
            cls._manager = Manager()
            cls._state = cls._manager.dict()
            cls._state["inboxes"] = cls._manager.list()
        return cls._state

    @classmethod
    def set_state(cls, state):
        cls._state = state

    @classmethod
    def publish(cls, identifier, event):
        for inbox in cls._state["inboxes"]:
            inbox.put(event)

    @classmethod
    def subscribe(cls, identifier, handler):
        cls._subscribers.setdefault(identifier, handler)
        cls._subscribers[identifier].add(handler)


class BaseWindow:

    def __init__(self, identifier, state):
        self.identifier = identifier
        self.state = state
        self._handlers = {}

    def subscribe(self, identifier, handler):
        self._handlers.setdefault(identifier, set())
        self._handlers.add()

    def receive_events(self):
        while not self.inbox.empty():
            event = self.inbox.get()
