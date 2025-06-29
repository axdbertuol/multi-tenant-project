from abc import ABC, abstractmethod
from typing import Any


class UnitOfWork(ABC):
    _repositories: dict[str, Any] = {}

    @abstractmethod
    def __enter__(self) -> "UnitOfWork":
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    @abstractmethod
    def commit(self) -> None:
        pass

    @abstractmethod
    def rollback(self) -> None:
        pass

    @abstractmethod
    def get_repository(self, name: str) -> Any:
        pass
