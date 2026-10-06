import asyncio


class WorkerState:
    def __init__(self):
        self.is_processing = False
        self.task: asyncio.Task | None = None
        self._subscribers: set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)

    def notify(self) -> None:
        payload = {"processing": self.is_processing}
        for queue in self._subscribers:
            queue.put_nowait(payload)