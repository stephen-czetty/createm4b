"""Class for encapsulating a book to be created"""

import ffmpeg
import tempfile
import os
from shutil import copyfile
from . import audiosourcefactory


class Book:
    """Class for encapsulating a book to be created"""

    @property
    def audio_list(self):
        """Get list of mp3s associated with this book"""
        return self.__audio_list

    @property
    def cover(self):
        """Get the filename for the cover image"""
        return self.__cover

    def convert(self, output_file, context):
        """Convert the book to an m4b"""
        (tfd, temp_name) = tempfile.mkstemp(suffix=".m4a", dir=context.working_directory)
        os.close(tfd)

        f = ffmpeg
        for i in (ffmpeg.input(mp3.file_name) for mp3 in self.__audio_list):
            f = f.concat(i, a=1, v=0)

        o = f.output(temp_name,
                     acodec="aac",
                     ab="64k",
                     ar="44100",
                     threads=3,
                     f="mp4",
                     map_metadata=-1,
                     strict="experimental")\
            .overwrite_output()

        context.print_verbose("ffmpeg arguments: {0}".format(o.get_args()))
        o.run(cmd="../ffmpeg")

        copyfile(temp_name, output_file)

    def __init__(self, input_files, cover_image=None):
        self.__audio_list = [audiosourcefactory.get_audio_source(file) for file in input_files]
        self.__cover = cover_image
