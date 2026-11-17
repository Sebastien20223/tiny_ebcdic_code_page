# tiny_ebcdic_code_page

Decodes and encodes IBM EBCDIC code page 037 (CP037), the single-byte code
page used for mainframe data interchange.

## Usage

```python
from tiny_ebcdic_code_page import decode_bytes, encode_bytes, codec_info

raw = b"\xc8\xc5\xd3\xd3\xd6"          # EBCDIC for "HELLO"
text = decode_bytes(raw)
assert text == "HELLO"
assert encode_bytes(text) == raw

print(codec_info())
# {'name': 'IBM037', 'aliases': ['cp037', 'IBM037', 'EBCDIC-CP-US'],
#  'bytes': 256, 'single_byte': True}
```

## Why this exists

Python's standard library already ships a `cp037` codec, but it is not
available in every runtime that needs to read mainframe data, and its
behaviour around unmappable input is easy to get wrong.  This module
implements the CP037 table by hand so the mapping is identical everywhere
and the failure mode is explicit: unmappable input raises
`EBCDICUnmappableError` rather than silently substituting a replacement
character.  The trade-off is that the table is a fixed snapshot of CP037;
adding another code page means adding another table, not reusing a general
codec framework.

## The awkward edge

CP037 is a single-byte code page, so every byte `0x00`–`0xFF` maps to exactly
one Unicode code point and back.  That means `decode_bytes(bytes(range(256)))`
succeeds and produces 256 characters, including control characters such as
`0x05` (HT) and `0x0D` (CR).  If you are decoding fixed-width mainframe
records, do not assume the result is printable text — strip or translate the
control characters yourself before display.

## API

All names below are exported from `tiny_ebcdic_code_page`.

- `decode(data: str) -> str` — decode a string whose code points are in
  `range(256)` into Unicode.  Raises `EBCDICUnmappableError` for code points
  above `0xFF`.
- `encode(text: str) -> str` — encode Unicode into a string of code points in
  `range(256)`.  Raises `EBCDICUnmappableError` for characters with no CP037
  mapping.
- `decode_bytes(data: bytes) -> str` — decode raw EBCDIC bytes.
- `encode_bytes(text: str) -> bytes` — encode Unicode into raw EBCDIC bytes.
- `codec_info() -> dict` — metadata about the codec; returns a fresh dict.
- `EBCDICError` — base class for errors from this module (subclass of
  `ValueError`).
- `EBCDICUnmappableError` — raised for unmappable input; carries `.value` and
  `.kind`.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

