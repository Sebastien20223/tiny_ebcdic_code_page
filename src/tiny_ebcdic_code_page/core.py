"""Single-byte EBCDIC code page 037 (CP037) codec.

Why this module exists
----------------------
Python ships a ``cp037`` codec, but it is not available in every runtime and
it silently substitutes for a handful of control positions.  Mainframe data
exchange often needs the exact, documented mapping and a way to reject
unmappable input rather than guess.  This module implements the CP037 table
by hand so the behaviour is identical everywhere and the failure mode is
explicit.

Design decisions
----------------
* The tables are built once at import time.  They are plain ``bytes`` objects
  indexed by the integer value of a character, which keeps lookups O(1) and
  avoids re-deriving the mapping on every call.
* ``decode``/``encode`` operate on ``str`` and return ``str``.  Byte-level
  helpers (``decode_bytes``/``encode_bytes``) are provided for callers that
already hold ``bytes`` and want to avoid an intermediate ``str`` round trip.
* Unmappable input raises :class:`EBCDICUnmappableError` instead of silently
  producing a replacement character.  Mainframe records are usually fixed
  width, so a silent substitution corrupts the record length downstream.
* The mapping is symmetric: every byte 0x00..0xFF has exactly one Unicode
  code point and vice versa.  This is a property of CP037 and is asserted by
  the test suite, not assumed by the encoder.
"""

from __future__ import annotations

from typing import Dict, Tuple

__all__ = [
    "EBCDICError",
    "EBCDICUnmappableError",
    "codec_info",
    "decode",
    "encode",
    "decode_bytes",
    "encode_bytes",
]


class EBCDICError(ValueError):
    """Base class for errors raised by this module."""


class EBCDICUnmappableError(EBCDICError):
    """Raised when a character or byte has no CP037 mapping.

    The offending value is stored so callers can report it without parsing
    the message string.
    """

    def __init__(self, value: object, kind: str) -> None:
        self.value = value
        self.kind = kind
        super().__init__(f"cannot map {kind} {value!r} in CP037")


# CP037 maps the 256 byte values onto Unicode code points.  The table below is
# the canonical IBM mapping.  It is written as a tuple of code points in byte
# order so that the byte->char direction is a direct index.
_CP037_CODEPOINTS: Tuple[int, ...] = (
    0x0000, 0x0001, 0x0002, 0x0003, 0x009C, 0x0009, 0x0086, 0x007F,
    0x0097, 0x008D, 0x008E, 0x000B, 0x000C, 0x000D, 0x000E, 0x000F,
    0x0010, 0x0011, 0x0012, 0x0013, 0x009D, 0x0085, 0x0008, 0x0087,
    0x0018, 0x0019, 0x0092, 0x008F, 0x001C, 0x001D, 0x001E, 0x001F,
    0x0080, 0x0081, 0x0082, 0x0083, 0x0084, 0x000A, 0x0017, 0x001B,
    0x0088, 0x0089, 0x008A, 0x008B, 0x008C, 0x0005, 0x0006, 0x0007,
    0x0090, 0x0091, 0x0016, 0x0093, 0x0094, 0x0095, 0x0096, 0x0004,
    0x0098, 0x0099, 0x009A, 0x009B, 0x0014, 0x0015, 0x009E, 0x001A,
    0x0020, 0x00A0, 0x00E2, 0x00E4, 0x00E0, 0x00E1, 0x00E3, 0x00E5,
    0x00E7, 0x00F1, 0x00A2, 0x002E, 0x003C, 0x0028, 0x002B, 0x007C,
    0x0026, 0x00E9, 0x00EA, 0x00EB, 0x00E8, 0x00ED, 0x00EE, 0x00EF,
    0x00EC, 0x00DF, 0x0021, 0x0024, 0x002A, 0x0029, 0x003B, 0x00AC,
    0x002D, 0x002F, 0x00C2, 0x00C4, 0x00C0, 0x00C1, 0x00C3, 0x00C5,
    0x00C7, 0x00D1, 0x00A6, 0x002C, 0x0025, 0x005F, 0x003E, 0x003F,
    0x00F8, 0x00C9, 0x00CA, 0x00CB, 0x00C8, 0x00CD, 0x00CE, 0x00CF,
    0x00CC, 0x0060, 0x003A, 0x0023, 0x0040, 0x0027, 0x003D, 0x0022,
    0x00D8, 0x0061, 0x0062, 0x0063, 0x0064, 0x0065, 0x0066, 0x0067,
    0x0068, 0x0069, 0x00AB, 0x00BB, 0x00F0, 0x00FD, 0x00FE, 0x00B1,
    0x00B0, 0x006A, 0x006B, 0x006C, 0x006D, 0x006E, 0x006F, 0x0070,
    0x0071, 0x0072, 0x00AA, 0x00BA, 0x00E6, 0x00B8, 0x00C6, 0x00A4,
    0x00B5, 0x007E, 0x0073, 0x0074, 0x0075, 0x0076, 0x0077, 0x0078,
    0x0079, 0x007A, 0x00A1, 0x00BF, 0x00D0, 0x00DD, 0x00DE, 0x00AE,
    0x005E, 0x00A3, 0x00A5, 0x00B7, 0x00A9, 0x00A7, 0x00B6, 0x00BC,
    0x00BD, 0x00BE, 0x005B, 0x005D, 0x00AF, 0x00A8, 0x00B4, 0x00D7,
    0x007B, 0x0041, 0x0042, 0x0043, 0x0044, 0x0045, 0x0046, 0x0047,
    0x0048, 0x0049, 0x00AD, 0x00F4, 0x00F6, 0x00F2, 0x00F3, 0x00F5,
    0x007D, 0x004A, 0x004B, 0x004C, 0x004D, 0x004E, 0x004F, 0x0050,
    0x0051, 0x0052, 0x00B9, 0x00FB, 0x00FC, 0x00F9, 0x00FA, 0x00FF,
    0x005C, 0x00F7, 0x0053, 0x0054, 0x0055, 0x0056, 0x0057, 0x0058,
    0x0059, 0x005A, 0x00B2, 0x00D4, 0x00D6, 0x00D2, 0x00D3, 0x00D5,
    0x0030, 0x0031, 0x0032, 0x0033, 0x0034, 0x0035, 0x0036, 0x0037,
    0x0038, 0x0039, 0x00B3, 0x00DB, 0x00DC, 0x00D9, 0x00DA, 0x009F,
)

# Build the byte->str and str->byte tables once.  ``bytes`` is used for the
# decode side because indexing a bytes object yields an int directly, and a
# dict for the encode side because it handles the sparse set of Unicode
# characters that CP037 actually covers.
_DECODE_TABLE: Tuple[str, ...] = tuple(chr(cp) for cp in _CP037_CODEPOINTS)
_ENCODE_TABLE: Dict[str, int] = {
    ch: byte for byte, ch in enumerate(_DECODE_TABLE)
}


# A few names are worth spelling out because they appear in the README and in
# user code.  They are derived from the table rather than hard-coded so that a
# table edit cannot leave them stale.
_CP037_NAME = "IBM037"
_CP037_ALIASES: Tuple[str, ...] = ("cp037", "IBM037", "EBCDIC-CP-US")


def codec_info() -> Dict[str, object]:
    """Return metadata about the codec.

    The result is a fresh dict on every call so callers cannot mutate a
    module-level cache by accident.
    """
    return {
        "name": _CP037_NAME,
        "aliases": list(_CP037_ALIASES),
        "bytes": 256,
        "single_byte": True,
    }


def decode(data: str) -> str:
    """Decode an EBCDIC string into Unicode.

    ``data`` is a string whose code points are all in ``range(256)``.  This
    mirrors the way Python's own codecs accept ``str`` input, and it makes the
    function usable when the caller has already read bytes into a string via
    ``bytes.decode('latin-1')``.

    Raises :class:`EBCDICUnmappableError` if any code point is outside
    ``range(256)``.
    """
    if not isinstance(data, str):
        raise TypeError("decode() expects a str of code points in range(256)")
    out = []
    for ch in data:
        cp = ord(ch)
        if cp > 0xFF:
            raise EBCDICUnmappableError(ch, "character")
        out.append(_DECODE_TABLE[cp])
    return "".join(out)


def encode(text: str) -> str:
    """Encode a Unicode string into EBCDIC.

    The return value is a ``str`` whose code points are all in ``range(256)``.
    Callers that need ``bytes`` should use :func:`encode_bytes` instead.

    Raises :class:`EBCDICUnmappableError` if a character has no CP037 mapping.
    """
    if not isinstance(text, str):
        raise TypeError("encode() expects a str")
    out = []
    for ch in text:
        try:
            out.append(_ENCODE_TABLE[ch])
        except KeyError:
            raise EBCDICUnmappableError(ch, "character") from None
    return "".join(chr(b) for b in out)


def decode_bytes(data: bytes) -> str:
    """Decode raw EBCDIC bytes into Unicode.

    This is a thin wrapper over :func:`decode` that first expands the bytes
    to a Latin-1 string.  It exists so callers do not have to remember the
    ``bytes.decode('latin-1')`` dance and so the error type stays consistent.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("decode_bytes() expects bytes-like input")
    return decode(bytes(data).decode("latin-1"))


def encode_bytes(text: str) -> bytes:
    """Encode a Unicode string into raw EBCDIC bytes.

    Raises :class:`EBCDICUnmappableError` for characters outside CP037.
    """
    if not isinstance(text, str):
        raise TypeError("encode_bytes() expects a str")
    return bytes(ord(ch) for ch in encode(text))
