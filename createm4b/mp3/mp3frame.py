from typing import List

from .mp3error import Mp3Error


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
