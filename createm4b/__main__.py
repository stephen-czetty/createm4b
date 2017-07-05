"""Main entry point"""

import sys
import tempfile
import shutil

from . import context
from . import arguments

def setup_environment(commandline):
    """Create environment for conversion"""
    commandline.print_verbose("Creating environment for conversion")

    # Create a tempdir to work in
    context.working_dir = tempfile.mkdtemp()
    commandline.print_veryverbose("Working dir: {0}".format(context.working_dir))

    # Remove working directory
    commandline.print_veryverbose("Cleaning up: {0}".format(context.working_dir))
    shutil.rmtree(context.working_dir)

def main(args=None):
    """Main entry point"""

    if args is None:
        args = sys.argv[1:]

    commandline = arguments.Arguments(args)
    setup_environment(commandline)

if __name__ == "__main__":
    main()
    