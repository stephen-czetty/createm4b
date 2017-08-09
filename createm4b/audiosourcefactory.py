"""Factory for creating audio source instances"""
from .flac import Flac
from .mp3 import Mp3
from .audiosource import AudioSource
from .filevalidator import FileValidator


class AudioSourceFactory:
    def get_audio_source(self, file_name: str) -> AudioSource:
        # TODO: Mp3.is_valid gets called twice, once here, once in Mp3.__init__.
        if self.__mp3_validator.is_valid(file_name):
            return Mp3(self.__mp3_validator, file_name)
        if self.__flac_validator.is_valid(file_name):
            return Flac(self.__flac_validator, file_name)

        raise Exception("Error loading file {0}".format(file_name))

    def __init__(self, mp3_validator: FileValidator, flac_validator: FileValidator):
        self.__mp3_validator = mp3_validator
        self.__flac_validator = flac_validator

del Flac, Mp3, AudioSource, FileValidator