"""Class representing an mp3 file"""

from eyed3.mp3 import Mp3AudioFile
import io
from .audiosource import AudioSource


class Mp3(AudioSource):
    """mp3 file"""

    __file_name = None
    __tag = None
    __duration = None
    __id3 = None

    @property
    def title(self):
        """Title of the mp3 from id3 tag"""
        return self.__tag.title

    @property
    def duration(self):
        """Duration of the mp3, in seconds"""
        if self.__duration is None:
            f = open(self.__file_name, 'rb')
            if self.__id3 is None:
                self.__id3 = Mp3.__read_id3(f)
            else:
                f.seek(self.__id3.size)

            duration = 0.0
            data = f.read(4)
            while len(data) == 4:
                frame = Mp3Frame(data)
                duration += frame.frame_duration
                f.seek(frame.frame_length - 4, io.SEEK_CUR)
                data = f.read(4)
            self.__duration = duration

        return self.__duration

    @property
    def file_name(self):
        """File name this class is working with"""
        return self.__file_name

    @property
    def tags(self):
        if self.__id3 is None:
            f = open(self.__file_name, 'rb')
            self.__id3 = Mp3.__read_id3(f)

        return self.__id3

    def __init__(self, file_name):
        self.__file_name = file_name
        self.__tag = Mp3AudioFile(file_name).tag

    @staticmethod
    def is_valid(file_path):
        f = None
        # noinspection PyBroadException
        try:
            f = open(file_path, 'rb')

            # Skip over any id3 block, if it exists
            Mp3.__read_id3(f)

            try:
                block = f.read(4)
                frame = Mp3Frame(block)

                # Verify the next frame
                f.seek(frame.frame_length - 4, io.SEEK_CUR)
                block = f.read(4)
                Mp3Frame(block)
            except Mp3Exception:
                return False
        finally:
            if f is not None:
                f.close()

        return True

    @staticmethod
    def __read_id3(file_handle):
        block = file_handle.read(10)

        id3 = ID3Header(block)
        if id3.is_valid_id3:
            file_handle.seek(id3.size, io.SEEK_CUR)
        else:
            file_handle.seek(-10, io.SEEK_CUR)

        # Check for an id3v1 tag, and skip it or use it as the info if there's no v2 header.
        block = file_handle.read(3)
        try:
            if block.decode("ascii") == "TAG":
                block.extend(file_handle.read(125))
                if id3.is_valid_id3:
                    return id3
                    # TODO: Parse id3v1, return that.
        except UnicodeDecodeError:
            pass

        file_handle.seek(-3, io.SEEK_CUR)
        return id3


class Mp3Frame:
    __bitrate_chart = [
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

    __sample_rate_chart = [
        [44100, 22050, 11025],
        [48000, 24000, 12000],
        [32000, 16000, 8000]
    ]

    __sample_count_chart = [
        [384, 1152, 1152],
        [384, 1152, 576],
        [384, 1152, 576]
    ]

    @property
    def frame_length(self):
        return self.__frame_length

    @property
    def sample_rate(self):
        return self.__sample_rate

    @property
    def bitrate(self):
        return self.__bitrate

    @property
    def samples(self):
        return Mp3Frame.__sample_count_chart[self.__version_index][self.__layer_index]

    @property
    def frame_duration(self):
        return float(self.samples) / self.sample_rate

    def __init__(self, data):
        frame_hdr = data[0:4]
        if frame_hdr[0] != 255:
            raise Mp3Exception("Invalid Frame Sync")

        if frame_hdr[1] & 0xe0 != 0xe0:  # validate the rest of the frame_sync bits exist
            raise Mp3Exception("Invalid Frame Sync")

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
            raise Mp3Exception("Unknown MPEG version")

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
            raise Mp3Exception("Unknown MPEG Layer")

        bitrate_index = frame_hdr[2] >> 4
        if bitrate_index == 15:
            raise Mp3Exception("Unknown bitrate")

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
            raise Mp3Exception("Invalid bitrate")

        sample_rate_index = (frame_hdr[2] & 0xc) >> 2
        if sample_rate_index == 3:
            raise Mp3Exception("Invalid sample rate")

        self.__sample_rate = Mp3Frame.__sample_rate_chart[sample_rate_index][self.__version_index]

        padding = frame_hdr[2] & 2 == 2

        padding_length = 1 if padding else 0
        if self.__layer_index == 0:
            padding_length *= 4
            self.__frame_length = int((12 * self.__bitrate * 1000 / self.__sample_rate + padding_length) * 4)
        else:
            self.__frame_length = int(144 * self.__bitrate * 1000 / self.__sample_rate + padding_length)


class ID3Header:
    __id3_size = 0

    @property
    def is_valid_id3(self):
        return self.__is_id3

    @property
    def size(self):
        return self.__id3_size

    def __init__(self, data):
        if data[0:3].decode("ascii") != "ID3":
            self.__is_id3 = False
            return
        self.__is_id3 = True
        self.__id3_size = data[6] << 21 | data[7] << 14 | data[8] << 7 | data[9]


class Mp3Exception(Exception):
    pass
