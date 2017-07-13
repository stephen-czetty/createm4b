"""Main entry point"""

import sys
import tempfile
import shutil

from .runtime import RuntimeContext
from .book import Book


def setup_environment(context):
    """Create environment for conversion"""
    context.print_unlessquiet("Creating environment for conversion")

    # Create a tempdir to work in
    context.working_directory = tempfile.mkdtemp()
    context.print_veryverbose("Working dir: {0}".format(context.working_directory))

    # Remove working directory
    context.print_veryverbose("Cleaning up: {0}".format(context.working_directory))
    shutil.rmtree(context.working_directory)


def main(args=None):
    """Main entry point"""

    if args is None:
        args = sys.argv[1:]

    context = RuntimeContext(args)
    setup_environment(context)
    book = Book(context.input_files, context.cover_image)

    context.print_verbose("Input file durations:")
    for mp3 in book.mp3_list:
        context.print_verbose("{0} (duration: {1})".format(mp3.title, mp3.duration))

if __name__ == "__main__":
    main()
