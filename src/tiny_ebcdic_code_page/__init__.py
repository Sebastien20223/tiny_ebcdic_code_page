"""EBCDIC code page 037 encode/decode helpers.

Only the public names below are part of the supported surface. Everything
else lives in :mod:`tiny_ebcdic_code_page.core` and may change without notice.
"""

from .core import (
    EBCDICError,
    EBCDICUnmappableError,
    codec_info,
    decode,
    encode,
    decode_bytes,
    encode_bytes,
)

__all__ = [
    "EBCDICError",
    "EBCDICUnmappableError",
    "codec_info",
    "decode",
    "encode",
    "decode_bytes",
    "encode_bytes",
]

__version__ = "1.0.0"
