import asyncio


class WorkerState:
    def __init__(self):
        self.is_processing = False
        self.task: asyncio.Task | None = None