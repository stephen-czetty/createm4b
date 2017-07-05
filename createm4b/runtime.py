"""Runtime Context"""

import argparse

class RuntimeContext():
    """Class for storing context needed at runtime"""
    __verbosity = 0
    __working_directory = ""

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
    def working_directory(self):
        """Get the working directory"""
        return self.__working_directory

    @working_directory.setter
    def working_directory(self, value):
        self.__working_directory = value

    @staticmethod
    def __get_argument_parser():
        """Builds up an argparse.ArgumentParser"""
        parser = argparse.ArgumentParser()

        group = parser.add_mutually_exclusive_group()
        group.add_argument("-v", "--verbose", help="increase verbosity", action="count", default=0)
        group.add_argument("-q", "--quiet", help="be very quiet", action="store_true")
        return parser

    def __init__(self, args):
        parser = self.__get_argument_parser()
        parsed = parser.parse_args(args)
        self.__verbosity = -1 if parsed.quiet else parsed.verbose
