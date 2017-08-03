from unittest import TestCase
from createm4b import util


class UtilTests(TestCase):
    def test_parse_32bit_little_endian(self):
        data = b"\x58\xb9\xba\x8b"
        expected = 2344270168

        result = util.parse_32bit_little_endian(data)

        self.assertEqual(result, expected)
