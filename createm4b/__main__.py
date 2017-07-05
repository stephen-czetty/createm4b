"""Main entry point"""

import sys
import tempfile
import shutil

from . import runtime

def setup_environment(context):
    """Create environment for conversion"""
    context.print_verbose("Creating environment for conversion")

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

    context = runtime.RuntimeContext(args)
    setup_environment(context)

if __name__ == "__main__":
    main()
    