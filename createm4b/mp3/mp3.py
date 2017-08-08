from io import SEEK_CUR
from typing import Optional

from ..audiosource import AudioSource
from ..filevalidator import FileValidator
from .id3 import ID3Base, ID3
from .mp3error import Mp3Error
from .mp3frame import Mp3Frame


class Mp3(AudioSource):
    """mp3 file"""

    __file_name: Optional[str] = None
    __duration: Optional[float] = None
    __id3: Optional[ID3Base] = None

    @property
    def title(self) -> str:
        """Title of the mp3 from id3 tag"""
        return self.tags.title

    @property
    def artist(self) -> str:
        return self.tags.artist

    @property
    def album(self) -> str:
        return self.tags.album

    @property
    def track(self) -> int:
        return self.tags.track

    @property
    def duration(self) -> float:
        """Duration of the mp3, in seconds"""
        self.__duration = self.__duration or self.__get_duration()

        return self.__duration

    def __get_duration(self):
        f = open(self.__file_name, 'rb')
        if self.__id3 is None:
            self.__id3 = ID3.read_id3(f)
        else:
            f.seek(self.__id3.size + 10)

        duration = 0.0
        data = f.read(4)
        while len(data) == 4:
            frame = Mp3Frame(data)
            duration += frame.frame_duration
            f.seek(frame.frame_length - 4, SEEK_CUR)
            data = f.read(4)
        return duration

    @property
    def file_name(self) -> str:
        """File name this class is working with"""
        return self.__file_name

    @property
    def tags(self) -> ID3Base:
        self.__id3 = self.__id3 or self.__read_id3()

        return self.__id3

    def __read_id3(self):
        f = open(self.__file_name, 'rb')
        return ID3.read_id3(f)

    def __init__(self, mp3_validator: FileValidator, file_name: str):
        if not mp3_validator.is_valid(file_name):
            raise Mp3Error("file is not an mp3 file")
        self.__file_name = file_name
