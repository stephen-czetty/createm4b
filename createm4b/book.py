"""Class for encapsulating a book to be created"""

from .mp3 import Mp3

class Book:
    """Class for encapsulating a book to be created"""

    @property
    def mp3_list(self):
        return self.__mp3_list

    def __init__(self, input_files):
        self.__mp3_list = [Mp3(file.name) for file in input_files]
