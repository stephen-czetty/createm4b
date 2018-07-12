from typing import Optional, cast, Iterator

from ..filevalidator import FileValidator
from .flacerror import FlacError
from .flacmetadata import FlacMetadata, FlacMetadataStreamInfo, FlacMetadataVorbis
from ..audiosource import AudioSource


class Flac(AudioSource):
    __title: Optional[str] = None
    __artist: Optional[str] = None
    __album: Optional[str] = None
    __track: Optional[int] = None
    __metadata: Optional[FlacMetadata] = None

    @property
    def duration(self) -> float:
        """Duration of the flac, in seconds"""
        stream_info = cast(FlacMetadataStreamInfo, next(self.metadata("StreamInfo")))
        return float(stream_info.total_samples) / stream_info.sample_rate

    @property
    def file_name(self) -> str:
        return self.__file_name

    @property
    def title(self) -> str:
        self.__title = self.__title or self.__get_tag("TITLE")

        return self.__title

    @property
    def artist(self) -> str:
        self.__artist = self.__artist or self.__get_tag("ARTIST")

        return self.__artist

    @property
    def album(self) -> str:
        self.__album = self.__album or self.__get_tag("ALBUM")

        return self.__album

    @property
    def track(self) -> Optional[int]:
        if self.__track is None:
            try:
                # noinspection SpellCheckingInspection
                self.__track = int(self.__get_tag("TRACKNUMBER"))
            except (ValueError, TypeError):
                self.__track = None

        return self.__track

    def __get_tag(self, name: str) -> Optional[str]:
        comment_block = cast(Optional[FlacMetadataVorbis], next((self.metadata("VorbisComment")), None))
        return comment_block.tag(name) if comment_block else None

    def metadata(self, block_type: str) -> Iterator[FlacMetadata]:
        self.__metadata = self.__metadata or [f for f in Flac.get_metadata(self.__file_name)]
        return (x for x in self.__metadata if x.block_type == block_type)

    def __init__(self, flac_validator: FileValidator, file_name: str):
        if not flac_validator.is_valid(file_name):
            raise FlacError("{0} is not a flac file".format(file_name))

        self.__file_name = file_name

    @staticmethod
    def get_metadata(file_name: str) -> Iterator[FlacMetadata]:
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
