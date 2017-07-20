"""Class for encapsulating a book to be created"""

import ffmpeg
from . import audiosourcefactory


class Book:
    """Class for encapsulating a book to be created"""

    @property
    def audio_list(self):
        """Get list of mp3s associated with this book"""
        return self.__audio_list

    @property
    def cover(self):
        """Get the filename for the cover image"""
        return self.__cover.name

    def convert(self, output_file):
        """Convert the book to an m4b"""
        inputs = [ffmpeg.input(mp3.file_name) for mp3 in self.__audio_list]
        ffmpeg.concat(inputs).output(output_file, acodec="aac", ab="64k", ar="44100", threads=3, f="mp4").run()

    def __init__(self, input_files, cover=None):
        self.__audio_list = [audiosourcefactory.get_audio_source(file.name) for file in input_files]
        self.__cover = cover
