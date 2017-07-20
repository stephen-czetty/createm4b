"""Flac file support"""
from abc import ABC, abstractmethod

import ffprobe3

from .audiosource import AudioSource


class Flac(AudioSource):
    __duration = None

    @property
    def duration(self):
        """Duration of the mp3, in seconds"""
        if self.__duration is None:
            file_scan = ffprobe3.FFProbe(self.__file_name)
            self.__duration = file_scan.audio[0].duration

        return self.__duration

    @property
    def file_name(self):
        return self.__file_name

    @property
    def title(self):
        pass

    def __init__(self, file_name):
        if not Flac.is_valid(file_name):
            raise FlacException("{0} is not a flac file".format(file_name))

        self.__file_name = file_name

    @staticmethod
    def is_valid(file_name):
        f = None

        # noinspection PyBroadException
        try:
            f = open(file_name, "rb")
            block = f.read(1024)

            if block[0:4].decode("ascii") != "fLaC":
                return False

            position = 4
            metadata_block = FlacMetadata.read_metadata(block[position:])

            # The first block should always be a StreamInfo type
            if metadata_block.block_type != "StreamInfo":
                return False

            if not metadata_block.validate():
                return False

            while not metadata_block.last_block:
                if metadata_block.block_size + position > len(block):
                    position -= len(block)
                    block = f.read(metadata_block.block_size + 1024)
                position += metadata_block.block_size
                metadata_block = FlacMetadata.read_metadata(block[position:])
                if not metadata_block.validate():
                    return False
        except Exception:
            return False

        finally:
            if f is not None:
                f.close()

        return True


class FlacMetadata(ABC):
    @property
    @abstractmethod
    def block_type(self):
        pass

    @property
    def block_size(self):
        return self.__block_size

    @property
    def last_block(self):
        return self.__last_block

    @abstractmethod
    def validate(self):
        pass

    def __init__(self, data):
        self.__last_block = data[0] & 0x80 == 0x80
        self.__block_size = (data[1] << 16 | data[2] << 8 | data[3]) + 4

    @staticmethod
    def read_metadata(data):
        block_type = data[0] & 0x7f

        if block_type == 0:
            return FlacMetadataStreamInfo(data)
        if block_type == 4:
            return FlacMetadataVorbis(data)
        return FlacMetadataGeneric(data)


class FlacMetadataStreamInfo(FlacMetadata):
    @property
    def block_type(self):
        return "StreamInfo"

    def validate(self):
        if self.__sample_rate == 0:
            return False
        if self.__number_of_channels < 1 or self.__number_of_channels > 8:
            return False
        if self.__bits_per_sample < 4 or self.__bits_per_sample > 32:
            return False

        return True

    def __init__(self, data):
        super().__init__(data)
        self.__minimum_block_size = data[4] << 8 | data[5]
        self.__maximum_block_size = data[6] << 8 | data[7]
        self.__minimum_frame_size = data[8] << 16 | data[9] << 8 | data[10]
        self.__maximum_frame_size = data[11] << 16 | data[12] << 8 | data[13]
        self.__sample_rate = data[14] << 12 | data[15] << 4 | (data[16] & 0xf0) >> 4
        self.__number_of_channels = ((data[16] & 0x0e) >> 1) + 1
        self.__bits_per_sample = ((data[16] & 0x01) << 4 | (data[17] & 0xf0) >> 4) + 1
        self.__total_samples = (data[17] & 0x0f) << 32 | data[18] << 24 | data[19] << 16 | data[20] << 8 | data[21]
        self.__signature = data[22:38]


class FlacMetadataVorbis(FlacMetadata):
    def validate(self):
        return True

    @property
    def block_type(self):
        return "VorbisComment"

    def __init__(self, data):
        super().__init__(data)
        self.__data = data[4:self.block_size]


class FlacMetadataGeneric(FlacMetadata):
    def validate(self):
        return True

    @property
    def block_type(self):
        return "Unknown"

    def __init__(self, data):
        super().__init__(data)


class FlacException(Exception):
    pass
