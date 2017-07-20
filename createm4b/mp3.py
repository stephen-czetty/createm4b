"""Class representing an mp3 file"""

from eyed3.mp3 import isMp3File, Mp3AudioFile
import ffprobe3

from .audiosource import AudioSource


class Mp3(AudioSource):
    """mp3 file"""

    __file_name = None
    __tag = None
    __duration = None

    @property
    def title(self):
        """Title of the mp3 from id3 tag"""
        return self.__tag.title

    @property
    def duration(self):
        """Duration of the mp3, in seconds"""
        if self.__duration is None:
            file_scan = ffprobe3.FFProbe(self.__file_name)
            self.__duration = file_scan.audio[0].duration

        return self.__duration

    @property
    def file_name(self):
        """File name this class is working with"""
        return self.__file_name

    def __init__(self, file_name):
        if not isMp3File(file_name):
            raise Exception("{0} is not an mp3 file!".format(file_name))

        self.__file_name = file_name
        self.__tag = Mp3AudioFile(file_name).tag
