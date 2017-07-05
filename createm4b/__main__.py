"""Main entry point"""

import sys
import argparse
import tempfile
import shutil

from . import context

def get_argument_parser():
    """Builds up an argparse.ArgumentParser"""
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="increase verbosity", action="count", default=0)
    group.add_argument("-q", "--quiet", help="be very quiet", action="store_true")
    return parser

def print_unlessquiet(string):
    """Utility method to print unless --quiet is specified"""
    if context.verbosity >= 0:
        print(string)

def print_verbose(string):
    """Utility method to wrop check for verbosity"""
    if context.verbosity > 0:
        print(string)

def print_veryverbose(string):
    """Utility method for higher verbose messages"""
    if context.verbosity > 1:
        print(string)

def setup_environment():
    """Create environment for conversion"""
    print_verbose("Creating environment for conversion")

    # Create a tempdir to work in
    context.working_dir = tempfile.mkdtemp()
    print_veryverbose("Working dir: {0}".format(context.working_dir))

    # Remove working directory
    print_veryverbose("Cleaning up: {0}".format(context.working_dir))
    shutil.rmtree(context.working_dir)

def main(args=None):
    """Main entry point"""

    if args is None:
        args = sys.argv[1:]

    parser = get_argument_parser()
    args = parser.parse_args(args)
    context.verbosity = -1 if args.quiet else args.verbose

    setup_environment()

if __name__ == "__main__":
    main()
    