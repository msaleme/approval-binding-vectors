"""RFC 8785 JSON Canonicalization Scheme (JCS) — dependency-free.

The one canonicalizer in this corpus. check.py, generate.py, isolation.py and
weak_checker_demo.py all import it, so the digests the vectors carry and the
digests the checkers recompute cannot drift apart.

Input is the Python value json.loads() produces from I-JSON (RFC 7493):
dict with str keys, list, str, int, float, bool, None. Output is UTF-8 bytes.

  * Object members are sorted by their names as arrays of UTF-16 code units
    (RFC 8785 section 3.2.3), not by Unicode code point, which is what
    Python's sort_keys does. The two differ once names mix code points above
    U+FFFF with names in U+E000..U+FFFF.
  * Strings are emitted as-is except ", \\ and U+0000..U+001F (section 3.2.2.2).
    A lone surrogate is an error.
  * Numbers are IEEE 754 doubles serialized per ECMAScript Number::toString
    (section 3.2.2.3): 3.0 -> 3, 1e-07 -> 1e-7, 1e16 -> 10000000000000000,
    -0.0 -> 0. NaN and Infinity are errors. An int is converted to a double
    first, as a JavaScript parser would; an int outside double range is an error.

v0.1.0 to v0.1.2 used json.dumps(sort_keys=True, separators=(",", ":")). That
agrees with RFC 8785 on strings, booleans, null and integers up to 2**53, but not
on floats such as 3.0, 1e-07 or 1e+16, on -0.0, or on member order when names mix
code points above U+FFFF with U+E000..U+FFFF. It emits 3.0 where RFC 8785 emits 3,
so a record executing 3.0 against an approval over 3 was rejected (CTRL-04).
"""
from __future__ import annotations

import math

__all__ = ["canonicalize", "number"]

_SHORT = {0x08: "\\b", 0x09: "\\t", 0x0A: "\\n", 0x0C: "\\f", 0x0D: "\\r",
          0x22: '\\"', 0x5C: "\\\\"}


def _string(s: str) -> str:
    out = ['"']
    for ch in s:
        cp = ord(ch)
        if 0xD800 <= cp <= 0xDFFF:
            raise ValueError(f"lone surrogate U+{cp:04X} is not valid I-JSON (RFC 8785 3.2.2.2)")
        if cp in _SHORT:
            out.append(_SHORT[cp])
        elif cp < 0x20:
            out.append(f"\\u{cp:04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def number(x: int | float) -> str:
    """ECMAScript Number::toString(x) for a finite double (ECMA-262 7.1.12.1)."""
    if isinstance(x, int):
        try:
            x = float(x)
        except OverflowError:
            raise ValueError("integer outside IEEE 754 double range (RFC 8785 3.2.2.3)") from None
    if not math.isfinite(x):
        raise ValueError("NaN and Infinity are not permitted (RFC 8785 3.2.2.3)")
    if x == 0:
        return "0"  # also -0
    sign = "-" if x < 0 else ""
    # repr() gives the shortest digit string that round-trips, choosing the
    # closest (then even) candidate: the same digits ECMAScript requires.
    mantissa, _, exp = repr(abs(x)).partition("e")
    whole, _, frac = mantissa.partition(".")
    raw = whole + frac
    point = len(whole) + int(exp or 0)       # decimal point position within raw
    lead = len(raw) - len(raw.lstrip("0"))
    digits = raw.strip("0")
    k = len(digits)                          # ECMA-262: k digits s, value = s * 10^(n-k)
    n = point - lead
    if k <= n <= 21:
        body = digits + "0" * (n - k)
    elif 0 < n <= 21:
        body = digits[:n] + "." + digits[n:]
    elif -6 < n <= 0:
        body = "0." + "0" * (-n) + digits
    else:
        e = n - 1
        body = digits[0] + ("." + digits[1:] if k > 1 else "") + "e" + ("+" if e >= 0 else "-") + str(abs(e))
    return sign + body


def _utf16_key(name: str) -> bytes:
    # Big-endian UTF-16 compares bytewise exactly as its code units compare numerically.
    return name.encode("utf-16-be", "surrogatepass")


def _emit(v, out: list[str]) -> None:
    if v is None:
        out.append("null")
    elif v is True:
        out.append("true")
    elif v is False:
        out.append("false")
    elif isinstance(v, (int, float)):
        out.append(number(v))
    elif isinstance(v, str):
        out.append(_string(v))
    elif isinstance(v, (list, tuple)):
        out.append("[")
        for i, item in enumerate(v):
            if i:
                out.append(",")
            _emit(item, out)
        out.append("]")
    elif isinstance(v, dict):
        for name in v:
            if not isinstance(name, str):
                raise TypeError(f"object member name must be a string, got {type(name).__name__}")
        out.append("{")
        for i, name in enumerate(sorted(v, key=_utf16_key)):
            if i:
                out.append(",")
            out.append(_string(name))
            out.append(":")
            _emit(v[name], out)
        out.append("}")
    else:
        raise TypeError(f"not a JSON value: {type(v).__name__}")


def canonicalize(value) -> bytes:
    """RFC 8785 canonical form of `value`, as UTF-8 bytes."""
    out: list[str] = []
    _emit(value, out)
    return "".join(out).encode("utf-8")
