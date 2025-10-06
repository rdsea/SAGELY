import asyncio
from abc import ABC, abstractmethod
from typing import TypeVar
from drone.data.base_data_generator import BaseDataGenerator

T = TypeVar("T")


class BaseDataSender(ABC):
    def __init__(self, data_generator: BaseDataGenerator[T], frequency: int) -> None:
        self.data_generator = data_generator
        self.frequency = frequency
        self._task = None
        self._stop_event = asyncio.Event()

    @abstractmethod
    async def send(self):
        """Abstract method to be implemented by subclasses"""
        pass

    async def _run_periodically(self):
        """Runs the `send` method at the specified frequency"""
        while not self._stop_event.is_set():
            await self.send()  # Call the async send method
            await asyncio.sleep(1.0 / self.frequency)

    def start(self):
        """Starts the periodic sender task"""
        if self._task is None or self._task.done():
            self._stop_event.clear()
            self._task = asyncio.create_task(self._run_periodically())

    def stop(self):
        """Stops the periodic sender task"""
        if self._task:
            self._stop_event.set()
            self._task.cancel()
            self._task = None
