"""Class representing an mp3 file"""

from eyed3.mp3 import Mp3AudioFile
import ffprobe3

from .audiosource import AudioSource


class Mp3(AudioSource):
    """mp3 file"""

    __file_name = None
    __tag = None
    __duration = None

    @property
    def title(self):
        """Title of the mp3 from id3 tag"""
        return self.__tag.title

    @property
    def duration(self):
        """Duration of the mp3, in seconds"""
        if self.__duration is None:
            file_scan = ffprobe3.FFProbe(self.__file_name)
            self.__duration = file_scan.audio[0].duration

        return self.__duration

    @property
    def file_name(self):
        """File name this class is working with"""
        return self.__file_name

    def __init__(self, file_name):
        if not Mp3.is_valid(file_name):
            raise Exception("{0} is not an mp3 file!".format(file_name))

        self.__file_name = file_name
        self.__tag = Mp3AudioFile(file_name).tag

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
        [448, 384, 320, 256, 160]]

    __sample_rate_chart = [
        [44100, 22050, 11025],
        [48000, 24000, 12000],
        [32000, 16000, 8000]]

    @staticmethod
    def is_valid(file_path):
        f = None
        # noinspection PyBroadException
        try:
            f = open(file_path, 'rb')
            block = f.read(1024)
            # Check for an ID3 header
            if block[0:3].decode("ascii") == "ID3":
                id3_size = block[6] << 21 | block[7] << 14 | block[8] << 7 | block[9]
                if id3_size < 1024:
                    block = block[id3_size + 10:]
                else:
                    block = f.read(1024 * (int(id3_size / 1024) + 1))[id3_size - 1014:]

            frame_start = block.find(255)
            block_count = 0  # abort after 64k
            while len(block) > 0 and frame_start == -1 and block_count < 64:
                block = f.read(1024)
                frame_start = block.find(255)
                block_count += 1

            if frame_start > -1:
                frame_hdr = block[frame_start:frame_start + 4]
                if frame_hdr[0] != 255:
                    return False

                if frame_hdr[1] & 0xe0 != 0xe0:  # validate the rest of the frame_sync bits exist
                    return False

                version_id = (frame_hdr[1] & 0x18) >> 3
                if version_id == 0:
                    # mpeg_version = '2.5'
                    version_index = 2
                elif version_id == 2:
                    # mpeg_version = '2'
                    version_index = 1
                elif version_id == 3:
                    # mpeg_version = '1'
                    version_index = 0
                else:
                    return False

                layer_description = (frame_hdr[1] & 6) >> 1
                if layer_description == 1:
                    # layer_desc = 'Layer III'
                    layer_index = 2
                elif layer_description == 2:
                    # layer_desc = 'Layer II'
                    layer_index = 1
                elif layer_description == 3:
                    # layer_desc = 'Layer I'
                    layer_index = 0
                else:
                    return False

                bitrate_index = frame_hdr[2] >> 4
                if bitrate_index == 15:
                    return False

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
                bitrate_col = layer_index
                if version_index > 0:
                    bitrate_col += 3 + min(layer_index, 1)

                bitrate = Mp3.__bitrate_chart[bitrate_index][bitrate_col]
                if bitrate <= 0:
                    return False

                sample_rate_index = (frame_hdr[2] & 0xc) >> 2
                if sample_rate_index == 3:
                    return False

                sample_rate = Mp3.__sample_rate_chart[sample_rate_index][version_index]

                padding = frame_hdr[2] & 2 == 2

                padding_length = 1 if padding else 0
                if layer_index == 0:
                    padding_length *= 4
                    frame_length = int((12 * bitrate * 1000 / sample_rate + padding_length) * 4)
                else:
                    frame_length = int(144 * bitrate * 1000 / sample_rate + padding_length)

                # Verify the next frame
                if frame_start + frame_length < len(block):
                    if block[frame_start + frame_length] != 255:
                        return False
                else:
                    offset = (frame_start + frame_length) - len(block)
                    block = f.read(1024)
                    if len(block) <= offset or block[offset] != 255:
                        return False
        except:
            return False

        finally:
            if f is not None:
                f.close()

        return True
