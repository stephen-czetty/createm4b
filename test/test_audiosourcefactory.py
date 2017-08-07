from unittest import TestCase
from createm4b.audiosourcefactory import AudioSourceFactory
from createm4b.mp3 import Mp3
from createm4b.flac import Flac
from createm4b.filevalidator import FileValidator


class TrueValidator(FileValidator):
    def is_valid(self, file_name):
        return True


class FalseValidator(FileValidator):
    def is_valid(self, file_name):
        return False


class AudioSourceFactoryTests(TestCase):
    def test_when_mp3_is_valid_should_return_mp3_instance(self):
        factory = AudioSourceFactory(TrueValidator(), FalseValidator())

        result = factory.get_audio_source("")

        self.assertIsInstance(result, Mp3)

    def test_when_flac_is_valid_should_return_flac_instance(self):
        factory = AudioSourceFactory(FalseValidator(), TrueValidator())

        result = factory.get_audio_source("")

        self.assertIsInstance(result, Flac)

    def test_when_nothing_is_valid_should_raise_exception(self):
        factory = AudioSourceFactory(FalseValidator(), FalseValidator())

        with self.assertRaises(Exception):
            factory.get_audio_source("")
