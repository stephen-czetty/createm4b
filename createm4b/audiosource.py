"""Abstract class representing a single audio source file"""

from abc import ABC, abstractmethod
from typing import Optional


class AudioSource(ABC):  # pragma: no cover
    @property
    @abstractmethod
    def title(self) -> str:
        pass

    @property
    @abstractmethod
    def duration(self) -> float:
        pass

    @property
    @abstractmethod
    def file_name(self) -> str:
        pass

    @property
    @abstractmethod
    def artist(self) -> str:
        pass

    @property
    @abstractmethod
    def album(self) -> str:
        pass

    @property
    @abstractmethod
    def track(self) -> Optional[int]:
        pass


del ABC, abstractmethod, Optional
