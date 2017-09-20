from abc import ABC, abstractmethod


class FileValidator(ABC):  # pragma: no cover
    @abstractmethod
    def is_valid(self, file_name: str) -> bool:
        pass


del ABC, abstractmethod
