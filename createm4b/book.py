"""Class for encapsulating a book to be created"""

import ffmpeg
import tempfile
import os
import subprocess
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
        context.print_unlessquiet("Converting book to {0}".format(output_file))
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
                     strict="experimental") \
            .overwrite_output()

        context.print_verbose("ffmpeg arguments: {0}".format(o.get_args()))
        cmd = "../ffmpeg" if os.name == "nt" else "ffmpeg"
        o.run(cmd=cmd)

        # Rebuild with the metadata and (optional) cover image
        metadata_file = self.__create_metadata_file(context)

        (tfd, temp_name2) = tempfile.mkstemp(suffix=".m4a", dir=context.working_directory)
        os.close(tfd)
        args = [cmd, "-i", temp_name, "-i", metadata_file]

        if self.cover is not None:
            context.print_unlessquiet("Adding cover image (this may take some time)")

            args.extend(["-loop", "1", "-i", self.cover,
                         "-map", "2:0",
                         "-c:v", "libx264", "-tune", "stillimage", "-crf", "25", "-r", "1",
                         "-strict", "experimental",
                         "-threads", "3",
                         "-shortest"])

        args.extend(["-map_metadata", "1", "-map", "0:0", "-c:a", "copy", "-y", temp_name2])
        context.print_verbose("ffmpeg arguments: {0}".format(args))
        stdout = None if context.verbosity > 1 else subprocess.DEVNULL
        subprocess.run(args, stdout=stdout)

        copyfile(temp_name2, output_file)

    def __create_metadata_file(self, context):
        (fd, metadata_file) = tempfile.mkstemp(suffix=".txt", dir=context.working_directory)
        os.write(fd, ";FFMETADATA1\n".encode("utf8"))
        os.write(fd, "album={0}\n".format(Book.__metadata_escape(self.audio_list[0].album)).encode("utf8"))
        os.write(fd, "album_artist={0}\n".format(Book.__metadata_escape(self.audio_list[0].artist)).encode("utf8"))

        position = 0
        for track in self.audio_list:
            os.write(fd, "\n[CHAPTER]\nTIMEBASE=1/1000\n".encode("utf8"))
            os.write(fd, "START={0}\n".format(position).encode("utf8"))
            position += int(track.duration * 1000)
            os.write(fd, "END={0}\n".format(position).encode("utf8"))
            os.write(fd, "title={0}\n".format(Book.__metadata_escape(track.title)).encode("utf8"))
            position += 1

        os.close(fd)
        return metadata_file

    @staticmethod
    def __metadata_escape(s):
        s = s.replace("\\", "\\\\")
        s = s.replace("=", "\\=")
        s = s.replace(";", "\\;")
        s = s.replace("#", "\\#")
        s = s.replace("\n", "\\\n")

        return s

    def __init__(self, input_files, cover_image=None):
        self.__audio_list = [audiosourcefactory.get_audio_source(file) for file in input_files]
        self.__cover = cover_image
