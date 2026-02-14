import multiprocessing as ms
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class Event:
    type: str
    payload: dict[str, Any]
    uuid: str = field(default_factory=lambda: uuid4().hex[:6])


class Hub:
    def __init__(self):
        self.manager = ms.Manager()
        self.proxy = HubProxy(
            ms.Queue(),
            ms.Queue(),
            inboxes=self.manager.dict(),
            outboxes=self.manager.dict(),
        )

    def create_process(self, id, target, args, kwargs):
        kwargs["proxy"] = self.proxy
        kwargs["id"] = id
        self.proxy.inboxes[id] = ms.Queue()
        self.proxy.outboxes[id] = ms.Queue()
        proc = ms.Process(target, args, kwargs)
        proc.start()
        return proc


@dataclass
class HubProxy:
    hub_request: ms.Queue[Any]
    hub_response: ms.Queue[Any]
    inboxes: dict[str, ms.Queue[Any]]
    outboxes: dict[str, ms.Queue[Any]]

    def get_inbox(self, id: str) -> ms.Queue:
        if id in self.inboxes:
            return self.inboxes[id]

        # Send request for queue
        self.hub_request.put(Event("REQUEST_QUEUE", {"id": id}))
        self.inboxes[id] = self.hub_response.get()
        return self.inboxes[id]

    def get_outbox(self, id: str) -> ms.Queue:
        if id in self.outboxes:
            return self.outboxes[id]

        # Send request for queue
        self.hub_request.put(Event("REQUEST_QUEUE", {"id": id}))
        self.outboxes[id] = self.hub_response.get()
        return self.outboxes[id]

    def send_event(self, event, exclude_id: str | None) -> None:
        for id, queue in self.inboxes.items():
            if id != exclude_id:
                queue.put(event)

    def recv_event(self, id: str) -> Any:
        return self.outboxes[id].get()

    def create_process(self, id, target, args, kwargs):
        kwargs["proxy"] = self.proxy
        kwargs["id"] = id
        self.get_inbox(id)
        self.get_outbox(id)
        proc = ms.Process(target, args, kwargs)
        proc.start()
        return proc
