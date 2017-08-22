# createm4b

This project is my totally over-engineered python application intended for
combining multiple *.mp3* or *.flac* audiobook files into a single *.m4b* with
embedded chapters.

This is my first real python project, so there are probably a lot of weird
non-python gotchas in here, though I have been trying to refactor it as I learn
more.

## Usage

    usage: createm4b.py [-h] [-v | -q] [-c COVER] -o OUTPUT [-s] file [file ...]

    positional arguments:
      file                  input file(s)

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         increase verbosity
      -q, --quiet           be very quiet
      -c COVER, --cover COVER
                            path to cover image
      -o OUTPUT, --output OUTPUT
                            output filename
      -s, --sort            sort using file metadata


## Notes

* This requires at least python 3.6, mainly due to the use of type hints.
* I have included a windows binary for ffmpeg.  On other platforms, it is assumed that ffmpeg can be found in the path
* Please file a bug if you see anything that's not "correct" python.  I am still learning!