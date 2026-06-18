"""Base collector contract."""
from abc import ABC, abstractmethod


class BaseCollector(ABC):
    name: str = "base"
    source_system: str = "mock"

    @abstractmethod
    def collect(self) -> dict:
        """Return a dict mapping table name -> list[record dict]. Read-only."""
        raise NotImplementedError
