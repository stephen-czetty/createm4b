from abc import ABC, abstractmethod
from typing import Optional, Dict

from io import FileIO, SEEK_END, SEEK_SET

from createm4b import util
from .mp3error import Mp3Error


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
