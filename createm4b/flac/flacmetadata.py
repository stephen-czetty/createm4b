from abc import ABC, abstractmethod
from typing import List, Iterator, Optional

from io import FileIO

from createm4b import util
from .flacerror import FlacError


class FlacMetadata(ABC):
    @property
    @abstractmethod
    def block_type(self) -> str:  # pragma: no cover
        pass

    @property
    def block_size(self) -> int:
        return self.__block_size

    @property
    def last_block(self) -> bool:
        return self.__last_block

    @property
    def raw_data(self) -> bytes:
        return self.__data

    @abstractmethod
    def validate(self) -> bool:  # pragma: no cover
        pass

    def __init__(self, file_handle):
        data = file_handle.read(4)
        self.__last_block = data[0] & 0x80 == 0x80
        self.__block_size = (data[1] << 16 | data[2] << 8 | data[3]) + 4
        self.__data = data + file_handle.read(self.__block_size-4)

    @staticmethod
    def read_metadata(file_handle):
        data = file_handle.peek(1)
        block_type = data[0] & 0x7f

        if block_type == 0:
            return FlacMetadataStreamInfo(file_handle)
        if block_type == 4:
            return FlacMetadataVorbis(file_handle)
        return FlacMetadataGeneric(file_handle)


class FlacMetadataStreamInfo(FlacMetadata):
    @property
    def block_type(self) -> str:
        return "StreamInfo"

    @property
    def total_samples(self) -> int:
        return self.__total_samples

    @property
    def sample_rate(self) -> int:
        return self.__sample_rate

    def validate(self) -> bool:
        if self.__sample_rate == 0:
            return False
        if self.__number_of_channels < 1 or self.__number_of_channels > 8:
            return False
        if self.__bits_per_sample < 4 or self.__bits_per_sample > 32:
            return False

        return True

    def __init__(self, file_handle: FileIO):
        super().__init__(file_handle)
        self.__minimum_block_size = self.raw_data[4] << 8 | self.raw_data[5]
        self.__maximum_block_size = self.raw_data[6] << 8 | self.raw_data[7]
        self.__minimum_frame_size = self.raw_data[8] << 16 | self.raw_data[9] << 8 | self.raw_data[10]
        self.__maximum_frame_size = self.raw_data[11] << 16 | self.raw_data[12] << 8 | self.raw_data[13]
        self.__sample_rate = self.raw_data[14] << 12 | self.raw_data[15] << 4 | (self.raw_data[16] & 0xf0) >> 4
        self.__number_of_channels = ((self.raw_data[16] & 0x0e) >> 1) + 1
        self.__bits_per_sample = ((self.raw_data[16] & 0x01) << 4 | (self.raw_data[17] & 0xf0) >> 4) + 1
        self.__total_samples = (self.raw_data[17] & 0x0f) << 32 | self.raw_data[18] << 24 | self.raw_data[19] << 16 |\
            self.raw_data[20] << 8 | self.raw_data[21]
        self.__signature = self.raw_data[22:38]


class FlacMetadataVorbis(FlacMetadata):
    __comments: Optional[List[str]] = None

    def validate(self) -> bool:
        try:
            self.__get_comments()
        except FlacError:
            return False
        return True

    @property
    def block_type(self) -> str:
        return "VorbisComment"

    @property
    def comments(self) -> List[str]:
        self.__comments = self.__comments or [x for x in self.__get_comments()]
        return self.__comments

    def __get_comments(self) -> Iterator[str]:
        try:
            pos = 4
            vendor_length = util.parse_32bit_little_endian(self.raw_data[pos:])
            pos += vendor_length + 4
            comment_count = util.parse_32bit_little_endian(self.raw_data[pos:])
            pos += 4
            for x in range(comment_count):
                comment_length = util.parse_32bit_little_endian(self.raw_data[pos:])
                pos += 4
                yield self.raw_data[pos:pos + comment_length].decode("utf8")
                pos += comment_length
        except LookupError:
            raise FlacError

    def tag(self, tag_name: str) -> Optional[str]:
        tag = next((x for x in self.comments if x.startswith("{0}=".format(tag_name))), None)
        return tag[len(tag_name) + 1:] if tag is not None else None

    def __init__(self, file_handle):
        super().__init__(file_handle)


class FlacMetadataGeneric(FlacMetadata):
    def validate(self) -> bool:
        return True

    @property
    def block_type(self) -> str:
        return "Unknown"

    def __init__(self, file_handle: FileIO):
        super().__init__(file_handle)
