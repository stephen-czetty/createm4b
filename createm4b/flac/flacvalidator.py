from createm4b.filevalidator import FileValidator
from . import Flac, FlacError


class FlacValidator(FileValidator):
    def is_valid(self, file_name: str) -> bool:
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
