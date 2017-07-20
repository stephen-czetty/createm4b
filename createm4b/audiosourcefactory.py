"""Factory for creating audio source instances"""

from .mp3 import Mp3


def get_audio_source(file_name):
    return Mp3(file_name)
