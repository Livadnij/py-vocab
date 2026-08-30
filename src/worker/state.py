import asyncio

class WorkerState:
    def __init__(self):
        self.enabled = asyncio.Event()
        self.is_processing = False