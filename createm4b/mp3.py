"""MP3 file handling"""
from abc import ABC, abstractmethod
from io import SEEK_CUR, SEEK_END, SEEK_SET, FileIO
from typing import Optional, Dict, List

from createm4b import util
from .audiosource import AudioSource
from .filevalidator import FileValidator


class ID3Base(ABC):
    @property
    @abstractmethod
    def is_valid_id3(self) -> bool:
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        pass

    @property
    @abstractmethod
    def artist(self) -> str:
        pass

    @property
    @abstractmethod
    def album(self) -> str:
        pass

    @property
    @abstractmethod
    def year(self) -> Optional[int]:
        pass

    @property
    @abstractmethod
    def comments(self) -> str:
        pass

    @property
    @abstractmethod
    def track(self) -> Optional[int]:
        pass

    @property
    @abstractmethod
    def genre(self) -> str:
        pass

    @property
    @abstractmethod
    def size(self) -> int:
        pass


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


class Mp3Validator(FileValidator):
    def is_valid(self, file_path: str) -> bool:
        f = None

        # noinspection PyBroadException
        try:
            f = open(file_path, 'rb')

            # Skip over any id3 block, if it exists
            ID3.read_id3(f, True)

            try:
                block = f.read(4)
                frame = Mp3Frame(block)

                # Verify the next frame
                f.seek(frame.frame_length - 4, SEEK_CUR)
                block = f.read(4)
                Mp3Frame(block)
            except Mp3Error:
                return False
        finally:
            if f is not None:
                f.close()

        return True


class Mp3Frame:
    __bitrate_chart: List[List[int]] = [
        [0, 0, 0, 0, 0],
        [32, 32, 32, 32, 8],
        [64, 48, 40, 48, 16],
        [96, 56, 48, 56, 24],
        [128, 64, 56, 64, 32],
        [160, 80, 64, 80, 40],
        [192, 96, 80, 96, 40],
        [224, 112, 96, 112, 56],
        [256, 128, 112, 128, 64],
        [288, 160, 128, 144, 80],
        [320, 192, 160, 160, 96],
        [352, 224, 192, 176, 112],
        [384, 256, 224, 192, 128],
        [416, 320, 256, 224, 144],
        [448, 384, 320, 256, 160]
    ]

    __sample_rate_chart: List[List[int]] = [
        [44100, 22050, 11025],
        [48000, 24000, 12000],
        [32000, 16000, 8000]
    ]

    __sample_count_chart: List[List[int]] = [
        [384, 1152, 1152],
        [384, 1152, 576],
        [384, 1152, 576]
    ]

    @property
    def frame_length(self) -> int:
        return self.__frame_length

    @property
    def sample_rate(self) -> int:
        return self.__sample_rate

    @property
    def bitrate(self) -> int:
        return self.__bitrate

    @property
    def samples(self) -> int:
        return Mp3Frame.__sample_count_chart[self.__version_index][self.__layer_index]

    @property
    def frame_duration(self) -> float:
        return float(self.samples) / self.sample_rate

    def __init__(self, data: bytes):
        frame_hdr = data[0:4]
        if frame_hdr[0] != 255:
            raise Mp3Error("Invalid Frame Sync")

        if frame_hdr[1] & 0xe0 != 0xe0:  # validate the rest of the frame_sync bits exist
            raise Mp3Error("Invalid Frame Sync")

        version_id = (frame_hdr[1] & 0x18) >> 3
        if version_id == 0:
            self.__mpeg_version = '2.5'
            self.__version_index = 2
        elif version_id == 2:
            self.__mpeg_version = '2'
            self.__version_index = 1
        elif version_id == 3:
            self.__mpeg_version = '1'
            self.__version_index = 0
        else:
            raise Mp3Error("Unknown MPEG version")

        layer_description = (frame_hdr[1] & 6) >> 1
        if layer_description == 1:
            self.__layer_desc = 'Layer III'
            self.__layer_index = 2
        elif layer_description == 2:
            self.__layer_desc = 'Layer II'
            self.__layer_index = 1
        elif layer_description == 3:
            self.__layer_desc = 'Layer I'
            self.__layer_index = 0
        else:
            raise Mp3Error("Unknown MPEG Layer")

        bitrate_index = frame_hdr[2] >> 4
        if bitrate_index == 15:
            raise Mp3Error("Unknown bitrate")

        # if mpeg_version == '1':
        #     if layer_desc == 'Layer I':
        #         bitrate_col = 0
        #     elif layer_desc == 'Layer II':
        #         bitrate_col = 1
        #     else:
        #         bitrate_col = 2
        # else:
        #     if layer_desc == 'Layer I':
        #         bitrate_col = 3
        #     else:
        #         bitrate_col = 4
        bitrate_col = self.__layer_index
        if self.__version_index > 0:
            bitrate_col += 3 + min(self.__layer_index, 1)

        self.__bitrate = Mp3Frame.__bitrate_chart[bitrate_index][bitrate_col]
        if self.__bitrate <= 0:
            raise Mp3Error("Invalid bitrate")

        sample_rate_index = (frame_hdr[2] & 0xc) >> 2
        if sample_rate_index == 3:
            raise Mp3Error("Invalid sample rate")

        self.__sample_rate = Mp3Frame.__sample_rate_chart[sample_rate_index][self.__version_index]

        padding = frame_hdr[2] & 2 == 2

        padding_length = 1 if padding else 0
        if self.__layer_index == 0:
            padding_length *= 4
            self.__frame_length = int((12 * self.__bitrate * 1000 / self.__sample_rate + padding_length) * 4)
        else:
            self.__frame_length = int(144 * self.__bitrate * 1000 / self.__sample_rate + padding_length)


class ID3:
    @staticmethod
    def read_id3(file_handle: FileIO, skip_v1: bool=False) -> ID3Base:
        id3 = ID3v2(file_handle)
        if id3.is_valid_id3 or skip_v1:
            return id3

        # Check for an id3v1 tag
        current_file_position = file_handle.tell()
        file_handle.seek(-128, SEEK_END)
        block = file_handle.read(128)
        id3 = ID3v1(block)

        file_handle.seek(current_file_position, SEEK_SET)
        return id3


class ID3v2(ID3Base):
    __id3_size: int = 0

    @property
    def album(self) -> str:
        return self.__album

    @property
    def genre(self) -> str:
        return self.__genre

    @property
    def track(self) -> Optional[int]:
        return self.__track

    @property
    def year(self) -> Optional[int]:
        return self.__year

    @property
    def comments(self) -> Dict[str, str]:
        return self.__comments

    @property
    def title(self) -> str:
        return self.__title

    @property
    def artist(self) -> str:
        return self.__artist

    @property
    def is_valid_id3(self) -> bool:
        return self.__is_id3

    @property
    def size(self) -> int:
        return self.__id3_size

    # noinspection SpellCheckingInspection
    def __parse_id3_data(self):
        if self.__unsynchronisation:
            raise Mp3Error("Unsynchronisation bit is not supported.")

        position = 0
        self.__comments = {}
        d = self.__data
        if self.__extended_header:
            # Skip the extended header.
            size = util.parse_32bit_little_endian(d[0:4])
            position += 4 + size

        tag_size = 3 if self.__id3_version == 2 else 4

        while position < self.__id3_size:
            if self.__id3_size - position < 6:
                break

            # Read a frame header
            frame_type = d[position:position + tag_size].decode("ascii")
            raw_frame_size = d[position + tag_size:position + (tag_size * 2)]
            frame_size = util.parse_32bit_little_endian(raw_frame_size) if self.__id3_version > 2 \
                else (raw_frame_size[0] << 24 | raw_frame_size[1] << 16 | raw_frame_size[2])
            frame_flags = d[position + 8:position + 10] if self.__id3_version > 2 else b"\0\0"

            position += 6 if self.__id3_version == 2 else 10
            if ((not frame_type.startswith("T"))
                    and frame_type != "COMM"
                    and frame_type != "COM")\
                    or frame_flags[1] & 0xc0 > 0:
                # Not a frame we care about, or encrypted, or compressed
                position += frame_size
                continue

            data_size = frame_size - 1

            if frame_flags[1] & 0x20 > 0:
                # Group number is appended to the frame header, skip it.
                position += 1
                data_size -= 1

            # Text encoding byte
            encoding = d[position]
            position += 1

            language = None
            if frame_type == "COMM" or frame_type == "COM":
                language = d[position:position+3].decode("ascii")
                position += 3
                data_size -= 3

            decoded_text = ID3v2.__decode_id3_text(d[position:position + data_size], encoding)
            if frame_type == "TALB" or frame_type == "TAL":
                self.__album = decoded_text
            elif frame_type == "TIT2" or frame_type == "TT2":
                self.__title = decoded_text
            elif frame_type == "TPE1" or frame_type == "TP1":
                self.__artist = decoded_text
            elif frame_type == "TYE":
                try:
                    self.__year = int(decoded_text)
                except ValueError:
                    self.__year = None
            elif frame_type == "TDRC":
                try:
                    self.__year = int(decoded_text[0:4])
                except ValueError:
                    self.__year = None
            elif frame_type == "TRCK" or frame_type == "TRK":
                try:
                    self.__track = int(decoded_text.split("/")[0])
                except ValueError:
                    self.__track = None
            elif frame_type == "TCON" or frame_type == "TCO":
                self.__genre = ID3v2.__decode_genre(decoded_text)
            elif frame_type == "COMM" or frame_type == "COM":
                if language.lower() == "eng":
                    comments = decoded_text.split("\0")
                    self.__comments[comments[0]] = comments[1]

            position += data_size

    @staticmethod
    def __decode_genre(genre_text: str) -> str:
        if genre_text[0] == "(":
            # Version 2 format
            if genre_text[1] == "(":
                # escaped paren
                return genre_text[1:]
            close_paren = genre_text.find(")")
            numeric_genre = int(genre_text[1:close_paren])
            if len(genre_text[close_paren + 1:]) > 0 and (genre_text[close_paren + 1] != "("
                                                          or genre_text[close_paren + 1:close_paren + 2] == "(("):
                return genre_text[close_paren + 1:]
            return str(numeric_genre)

        genres = genre_text.split("\0")
        if len(genres) > 1:
            return genres[1]
        return genres[0]

    @staticmethod
    def __decode_id3_text(data: bytes, encoding: int) -> str:
        return data.decode(ID3v2.__get_encoding(encoding))[:-1]

    @staticmethod
    def __get_encoding(encoding: int) -> str:
        if encoding == 0:
            return "ascii"
        if encoding == 3:
            return "utf-8"
        return "utf-16"

    def __init__(self, file_handle: FileIO):
        data = file_handle.read(10)
        if data[0:3].decode("ascii") != "ID3":
            self.__is_id3 = False
            return

        self.__id3_size = data[6] << 21 | data[7] << 14 | data[8] << 7 | data[9]
        flags = data[5]
        self.__id3_version = int(data[3])
        self.__unsynchronisation = flags & 0x80 == 0x80
        self.__extended_header = flags & 0x40 == 0x40
        self.__experimental = flags & 0x20 == 0x20
        self.__is_id3 = flags & 0x1f == 0
        self.__data = file_handle.read(self.__id3_size)
        self.__parse_id3_data()


class ID3v1(ID3Base):
    __is_id3: bool = False

    @property
    def album(self) -> str:
        return self.__album

    @property
    def genre(self) -> str:
        return self.__genre

    @property
    def track(self) -> Optional[int]:
        return self.__track

    @property
    def year(self) -> Optional[int]:
        return self.__year

    @property
    def comments(self) -> Dict[str, str]:
        return self.__comments

    @property
    def title(self) -> str:
        return self.__title

    @property
    def artist(self) -> str:
        return self.__artist

    @property
    def is_valid_id3(self) -> bool:
        return self.__is_id3

    @property
    def size(self) -> int:
        return 0

    def __init__(self, data: bytes):
        try:
            if data[0:3].decode("ascii") == "TAG":
                self.__is_id3 = True
        except UnicodeDecodeError:
            return

        self.__comments = {}
        self.__title = data[3:30].decode("ascii")
        self.__artist = data[33:63].decode("ascii")
        self.__album = data[63:93].decode("ascii")
        self.__year = int(data[93:97].decode("ascii"))
        self.__comments["id3v1"] = data[97:127].decode("ascii")
        self.__track = int(data[127]) if data[126] == 0 else None  # id3v1.1
        self.__genre = str(int(data[128]))


class Mp3Error(Exception):
    pass
