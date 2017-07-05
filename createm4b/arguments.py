"""Arguments parser"""

import argparse

class Arguments():
    """Class for parsing the command line"""
    _verbosity = 0

    def print_unlessquiet(self, string):
        """Utility method to print unless --quiet is specified"""
        if self._verbosity >= 0:
            print(string)

    def print_verbose(self, string):
        """Utility method to wrop check for verbosity"""
        if self._verbosity > 0:
            print(string)

    def print_veryverbose(self, string):
        """Utility method for higher verbose messages"""
        if self._verbosity > 1:
            print(string)

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
        self._verbosity = -1 if parsed.quiet else parsed.verbose
