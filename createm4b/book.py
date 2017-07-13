"""Class for encapsulating a book to be created"""

from .mp3 import Mp3


class Book:
    """Class for encapsulating a book to be created"""

    @property
    def mp3_list(self):
        """Get list of mp3s associated with this book"""
        return self.__mp3_list

    @property
    def cover(self):
        """Get the filename for the cover image"""
        return self.__cover.name

    def convert(self):
        """Convert the book to an m4b"""
        pass

    def __init__(self, input_files, cover=None):
        self.__mp3_list = [Mp3(file.name) for file in input_files]
        self.__cover = cover
