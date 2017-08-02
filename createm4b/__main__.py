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


def cleanup(context):
    # Remove working directory
    context.print_veryverbose("Cleaning up: {0}".format(context.working_directory))
    shutil.rmtree(context.working_directory)


def main(args=None):
    """Main entry point"""
    args = args or sys.argv[1:]

    context = RuntimeContext(args)
    try:
        setup_environment(context)
        book = Book(context.input_files, context.cover_image, context.sort)

        context.print_veryverbose("Input file durations (this may take some time):")
        if context.verbosity > 1:
            for mp3 in book.audio_list:
                context.print_veryverbose("{0} (duration: {1})".format(mp3.title, mp3.duration))

        book.convert(context.output_file, context)
    finally:
        cleanup(context)

if __name__ == "__main__":
    main()
