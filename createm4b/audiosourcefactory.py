"""Factory for creating audio source instances"""
from .flac import Flac
from .mp3 import Mp3


def get_audio_source(file_name):
    # TODO: Mp3.is_valid gets called twice, once here, once in Mp3.__init__.
    if Mp3.is_valid(file_name):
        return Mp3(file_name)
    if Flac.is_valid(file_name):
        return Flac(file_name)

    raise Exception("Error loading file {0}".format(file_name))
