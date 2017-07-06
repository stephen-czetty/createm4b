"""Runtime Context"""

import argparse

class RuntimeContext:
    """Class for storing context needed at runtime"""
    __verbosity = 0
    __working_directory = None
    __cover_image = None

    def print_unlessquiet(self, string):
        """Utility method to print unless --quiet is specified"""
        if self.__verbosity >= 0:
            print(string)

    def print_verbose(self, string):
        """Utility method to wrop check for verbosity"""
        if self.__verbosity > 0:
            print(string)

    def print_veryverbose(self, string):
        """Utility method for higher verbose messages"""
        if self.__verbosity > 1:
            print(string)

    @property
    def verbosity(self):
        """Get the output verbosity"""
        return self.__verbosity

    @property
    def working_directory(self):
        """Get the working directory"""
        return self.__working_directory

    @working_directory.setter
    def working_directory(self, value):
        self.__working_directory = value

    @property
    def cover_image(self):
        """Get the filename for the cover image"""
        return self.__cover_image

    @staticmethod
    def __get_argument_parser():
        """Builds up an argparse.ArgumentParser"""
        parser = argparse.ArgumentParser()

        group = parser.add_mutually_exclusive_group()
        group.add_argument("-v", "--verbose", help="increase verbosity", action="count", default=0)
        group.add_argument("-q", "--quiet", help="be very quiet", action="store_true")
        parser.add_argument("-c", "--cover", help="path to cover image", default=None)
        parser.add_argument("-o", "--output", help="output filename", required=True,
                            type=argparse.FileType("w"))
        parser.add_argument("input_files", metavar="file", help="input file(s)", nargs="+",
                            type=argparse.FileType())

        return parser

    def __init__(self, args):
        parser = self.__get_argument_parser()
        parsed = parser.parse_args(args)
        self.__verbosity = -1 if parsed.quiet else parsed.verbose
        self.__cover_image = parsed.cover
