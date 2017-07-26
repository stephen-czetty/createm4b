"""Flac file support"""

from abc import ABC, abstractmethod
from . import util
from .audiosource import AudioSource


class Flac(AudioSource):
    __title = None

    @property
    def duration(self):
        """Duration of the flac, in seconds"""
        stream_info = next(self.metadata("StreamInfo"))
        return float(stream_info.total_samples) / stream_info.sample_rate

    @property
    def file_name(self):
        return self.__file_name

    @property
    def title(self):
        if self.__title is None:
            comment_block = next((self.metadata("VorbisComment")), None)
            if comment_block is not None:
                self.__title = comment_block.tag("TITLE")

        return self.__title

    def metadata(self, block_type):
        return (x for x in self.__metadata if x.block_type == block_type)

    def __init__(self, file_name):
        if not Flac.is_valid(file_name):
            raise FlacError("{0} is not a flac file".format(file_name))

        self.__file_name = file_name
        self.__metadata = [f for f in Flac.get_metadata(file_name)]

    @staticmethod
    def is_valid(file_name):
        try:
            metadata = [f for f in Flac.get_metadata(file_name)]
            if metadata[0].block_type != "StreamInfo":
                return False

            for m in metadata:
                if not m.validate():
                    return False

            return True

        except FlacError:
            return False

    @staticmethod
    def get_metadata(file_name):
        f = None

        # TODO: This will fail with large metadata blocks.  The spec allows for block sizes of up to 17mb!
        try:
            f = open(file_name, "rb")
            block = f.read(1024)

            if block[0:4].decode("ascii") != "fLaC":
                raise FlacError

            position = 4
            metadata_block = FlacMetadata.read_metadata(block[position:])

            yield metadata_block

            while not metadata_block.last_block:
                if metadata_block.block_size + position > len(block):
                    position -= len(block)
                    block = f.read(metadata_block.block_size + 1024)
                position += metadata_block.block_size
                metadata_block = FlacMetadata.read_metadata(block[position:])
                yield metadata_block

        finally:
            if f is not None:
                f.close()


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

    @property
    def raw_data(self):
        return self.__data

    @abstractmethod
    def validate(self):
        pass

    def __init__(self, data):
        self.__last_block = data[0] & 0x80 == 0x80
        self.__block_size = (data[1] << 16 | data[2] << 8 | data[3]) + 4
        self.__data = data[4:self.__block_size]

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

    @property
    def total_samples(self):
        return self.__total_samples

    @property
    def sample_rate(self):
        return self.__sample_rate

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
    __comments = None

    def validate(self):
        try:
            self.__get_comments()
        except FlacError:
            return False
        return True

    @property
    def block_type(self):
        return "VorbisComment"

    @property
    def comments(self):
        self.__comments = self.__comments or [x for x in self.__get_comments()]
        return self.__comments

    def __get_comments(self):
        try:
            pos = 0
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

    def tag(self, tag_name):
        tag = next((x for x in self.comments if x.startswith("{0}=".format(tag_name))), None)
        return tag[len(tag_name) + 1:] if tag is not None else None

    def __init__(self, data):
        super().__init__(data)


class FlacMetadataGeneric(FlacMetadata):
    def validate(self):
        return True

    @property
    def block_type(self):
        return "Unknown"

    def __init__(self, data):
        super().__init__(data)


class FlacError(Exception):
    pass
