from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar("T")


class BaseDataGenerator(ABC, Generic[T]):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def next(self) -> T:
        pass
