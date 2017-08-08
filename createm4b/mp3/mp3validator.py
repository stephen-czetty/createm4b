from io import SEEK_CUR

from createm4b.filevalidator import FileValidator
from .id3 import ID3
from .mp3error import Mp3Error
from .mp3frame import Mp3Frame


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
