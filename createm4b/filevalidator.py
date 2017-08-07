from abc import ABC, abstractmethod


class FileValidator(ABC):
    @abstractmethod
    def is_valid(self, file_name):
        pass
