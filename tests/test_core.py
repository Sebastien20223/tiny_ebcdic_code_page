"""Tests for tiny_ebcdic_code_page.core.

The tests exercise the public API and the awkward cases that actually occur
when moving data between a mainframe and a Unix host: control characters,
unmappable input, empty strings, and round-tripping every byte value.
"""

import unittest

from tiny_ebcdic_code_page import (
    EBCDICError,
    EBCDICUnmappableError,
    codec_info,
    decode,
    decode_bytes,
    encode,
    encode_bytes,
)


class TestCodecInfo(unittest.TestCase):
    def test_name_and_aliases(self):
        info = codec_info()
        self.assertEqual(info["name"], "IBM037")
        self.assertIn("cp037", info["aliases"])
        self.assertTrue(info["single_byte"])
        self.assertEqual(info["bytes"], 256)

    def test_returns_fresh_dict(self):
        first = codec_info()
        first["name"] = "mutated"
        second = codec_info()
        self.assertEqual(second["name"], "IBM037")


class TestDecode(unittest.TestCase):
    def test_known_letters(self):
        # 0xC1..0xC9 are A..I in CP037.
        self.assertEqual(decode("\xc1\xc2\xc3"), "ABC")

    def test_digits(self):
        # 0xF0..0xF9 are 0..9 in CP037.
        self.assertEqual(decode("\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9"), "0123456789")

    def test_space_and_period(self):
        self.assertEqual(decode("\x40\x4b"), " .")

    def test_empty_string(self):
        self.assertEqual(decode(""), "")

    def test_high_code_point_rejected(self):
        with self.assertRaises(EBCDICUnmappableError) as ctx:
            decode("\u0100")
        self.assertEqual(ctx.exception.value, "\u0100")
        self.assertEqual(ctx.exception.kind, "character")

    def test_non_string_rejected(self):
        with self.assertRaises(TypeError):
            decode(b"\xc1")  # type: ignore[arg-type]


class TestEncode(unittest.TestCase):
    def test_known_letters(self):
        self.assertEqual(encode("ABC"), "\xc1\xc2\xc3")

    def test_digits(self):
        self.assertEqual(encode("0123456789"), "\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9")

    def test_empty_string(self):
        self.assertEqual(encode(""), "")

    def test_unmappable_character(self):
        # The Euro sign is not in CP037.
        with self.assertRaises(EBCDICUnmappableError) as ctx:
            encode("\u20ac")
        self.assertEqual(ctx.exception.value, "\u20ac")
        self.assertEqual(ctx.exception.kind, "character")

    def test_non_string_rejected(self):
        with self.assertRaises(TypeError):
            encode(b"ABC")  # type: ignore[arg-type]


class TestBytesHelpers(unittest.TestCase):
    def test_decode_bytes(self):
        self.assertEqual(decode_bytes(b"\xc1\xc2\xc3"), "ABC")

    def test_encode_bytes(self):
        self.assertEqual(encode_bytes("ABC"), b"\xc1\xc2\xc3")

    def test_decode_bytes_rejects_str(self):
        with self.assertRaises(TypeError):
            decode_bytes("ABC")  # type: ignore[arg-type]

    def test_encode_bytes_rejects_bytes(self):
        with self.assertRaises(TypeError):
            encode_bytes(b"ABC")  # type: ignore[arg-type]

    def test_bytearray_accepted(self):
        self.assertEqual(decode_bytes(bytearray(b"\xc1\xc2")), "AB")

    def test_memoryview_accepted(self):
        self.assertEqual(decode_bytes(memoryview(b"\xc1\xc2")), "AB")


class TestRoundTrip(unittest.TestCase):
    def test_every_byte_round_trips(self):
        # CP037 is a single-byte code page: every byte value must decode to
        # exactly one character and encode back to the same byte.
        raw = bytes(range(256))
        text = decode_bytes(raw)
        self.assertEqual(len(text), 256)
        self.assertEqual(encode_bytes(text), raw)

    def test_control_characters_preserved(self):
        # 0x05 is HT in CP037; 0x0D is CR.  These must survive a round trip.
        self.assertEqual(decode_bytes(b"\x05\x0d"), "\t\r")
        self.assertEqual(encode_bytes("\t\r"), b"\x05\x0d")

    def test_hello_world_round_trip(self):
        text = "Hello, World!"
        self.assertEqual(decode_bytes(encode_bytes(text)), text)


class TestExceptionHierarchy(unittest.TestCase):
    def test_unmappable_is_ebcdic_error(self):
        self.assertTrue(issubclass(EBCDICUnmappableError, EBCDICError))
        self.assertTrue(issubclass(EBCDICError, ValueError))

    def test_catching_base_class(self):
        try:
            encode("\u20ac")
        except EBCDICError:
            pass
        else:
            self.fail("expected EBCDICError")


if __name__ == "__main__":
    unittest.main()
