"""Abstract class representing a single audio source file"""

from abc import ABC, abstractmethod


class AudioSource(ABC):
    @property
    @abstractmethod
    def title(self):
        pass

    @property
    @abstractmethod
    def duration(self):
        pass

    @property
    @abstractmethod
    def file_name(self):
        pass

    @property
    @abstractmethod
    def artist(self):
        pass

    @property
    @abstractmethod
    def album(self):
        pass

    @property
    @abstractmethod
    def track(self):
        pass
