"""Flac file support"""

from abc import ABC, abstractmethod
from . import util
from .audiosource import AudioSource


class Flac(AudioSource):
    __title = None
    __artist = None
    __album = None
    __track = None

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
            self.__title = self.__get_tag("TITLE")

        return self.__title

    @property
    def artist(self):
        if self.__artist is None:
            self.__artist = self.__get_tag("ARTIST")

        return self.__artist

    @property
    def album(self):
        if self.__album is None:
            self.__album = self.__get_tag("ALBUM")

        return self.__album

    @property
    def track(self):
        if self.__track is None:
            try:
                # noinspection SpellCheckingInspection
                self.__track = int(self.__get_tag("TRACKNUMBER"))
            except (ValueError, TypeError):
                self.__track = 0

        return self.__track

    def __get_tag(self, name):
        comment_block = next((self.metadata("VorbisComment")), None)
        return comment_block.tag(name) if comment_block is not None else None

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

        try:
            f = open(file_name, "rb")
            block = f.read(4)

            if block.decode("ascii") != "fLaC":
                raise FlacError

            metadata_block = FlacMetadata.read_metadata(f)

            yield metadata_block

            while not metadata_block.last_block:
                metadata_block = FlacMetadata.read_metadata(f)
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

    def __init__(self, file_handle):
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

    def tag(self, tag_name):
        tag = next((x for x in self.comments if x.startswith("{0}=".format(tag_name))), None)
        return tag[len(tag_name) + 1:] if tag is not None else None

    def __init__(self, file_handle):
        super().__init__(file_handle)


class FlacMetadataGeneric(FlacMetadata):
    def validate(self):
        return True

    @property
    def block_type(self):
        return "Unknown"

    def __init__(self, file_handle):
        super().__init__(file_handle)


class FlacError(Exception):
    pass
