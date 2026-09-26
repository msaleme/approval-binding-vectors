#!/usr/bin/env python3
"""jcs.py against the values RFC 8785 itself publishes. Dependency-free.

Every expected value below is copied from the RFC text
(https://www.rfc-editor.org/rfc/rfc8785.txt), not produced by jcs.py, so a
pass is agreement with the RFC authors rather than with this repository.

    python3 -m unittest test_jcs -v
"""
from __future__ import annotations

import json
import struct
import unittest

from jcs import canonicalize, number


def f64(hex16: str) -> float:
    return struct.unpack(">d", bytes.fromhex(hex16))[0]


# RFC 8785 Appendix B, Table 1: IEEE 754 bit pattern -> JSON representation.
APPENDIX_B = [
    ("0000000000000000", "0"),
    ("8000000000000000", "0"),
    ("0000000000000001", "5e-324"),
    ("8000000000000001", "-5e-324"),
    ("7fefffffffffffff", "1.7976931348623157e+308"),
    ("ffefffffffffffff", "-1.7976931348623157e+308"),
    ("4340000000000000", "9007199254740992"),
    ("c340000000000000", "-9007199254740992"),
    ("4430000000000000", "295147905179352830000"),
    ("44b52d02c7e14af5", "9.999999999999997e+22"),
    ("44b52d02c7e14af6", "1e+23"),
    ("44b52d02c7e14af7", "1.0000000000000001e+23"),
    ("444b1ae4d6e2ef4e", "999999999999999700000"),
    ("444b1ae4d6e2ef4f", "999999999999999900000"),
    ("444b1ae4d6e2ef50", "1e+21"),
    ("3eb0c6f7a0b5ed8c", "9.999999999999997e-7"),
    ("3eb0c6f7a0b5ed8d", "0.000001"),
    ("41b3de4355555553", "333333333.3333332"),
    ("41b3de4355555554", "333333333.33333325"),
    ("41b3de4355555555", "333333333.3333333"),
    ("41b3de4355555556", "333333333.3333334"),
    ("41b3de4355555557", "333333333.33333343"),
    ("becbf647612f3696", "-0.0000033333333333333333"),
    ("43143ff3c1cb0959", "1424953923781206.2"),
]

# RFC 8785 sections 3.2.2 to 3.2.4: the worked example, input and final UTF-8 bytes.
# Written with '~' for the backslash so no editor or tool can pre-decode the escapes;
# after .replace() this is the RFC's input text verbatim.
SECTION_3_2_INPUT = r'''{
  "numbers": [333333333.33333329, 1E30, 4.50,
              2e-3, 0.000000000000000000000000001],
  "string": "~u20ac$~u000F~u000aA'~u0042~u0022~u005c~~~"~/",
  "literals": [null, true, false]
}'''.replace("~", "\\")
SECTION_3_2_4_HEX = """
7b 22 6c 69 74 65 72 61 6c 73 22 3a 5b 6e 75 6c 6c 2c 74 72
75 65 2c 66 61 6c 73 65 5d 2c 22 6e 75 6d 62 65 72 73 22 3a
5b 33 33 33 33 33 33 33 33 33 2e 33 33 33 33 33 33 33 2c 31
65 2b 33 30 2c 34 2e 35 2c 30 2e 30 30 32 2c 31 65 2d 32 37
5d 2c 22 73 74 72 69 6e 67 22 3a 22 e2 82 ac 24 5c 75 30 30
30 66 5c 6e 41 27 42 5c 22 5c 5c 5c 5c 5c 22 2f 22 7d
"""

# RFC 8785 section 3.2.3: sorting test data and the expected value order.
SECTION_3_2_3_INPUT = r'''{
  "~u20ac": "Euro Sign",
  "~r": "Carriage Return",
  "~ufb33": "Hebrew Letter Dalet With Dagesh",
  "1": "One",
  "~ud83d~ude00": "Emoji: Grinning Face",
  "~u0080": "Control",
  "~u00f6": "Latin Small Letter O With Diaeresis"
}'''.replace("~", "\\")
SECTION_3_2_3_ORDER = [
    "Carriage Return",
    "One",
    "Control",
    "Latin Small Letter O With Diaeresis",
    "Euro Sign",
    "Emoji: Grinning Face",
    "Hebrew Letter Dalet With Dagesh",
]


class AppendixB(unittest.TestCase):
    def test_number_samples(self):
        for bits, want in APPENDIX_B:
            with self.subTest(bits=bits):
                self.assertEqual(number(f64(bits)), want)

    def test_nan_and_infinity_are_errors(self):
        for bits in ("7fffffffffffffff", "7ff0000000000000"):
            with self.subTest(bits=bits), self.assertRaises(ValueError):
                number(f64(bits))


class WorkedExample(unittest.TestCase):
    def test_section_3_2_4_bytes(self):
        want = bytes.fromhex("".join(SECTION_3_2_4_HEX.split()))
        self.assertEqual(canonicalize(json.loads(SECTION_3_2_INPUT)), want)

    def test_section_3_2_3_sort_order(self):
        out = canonicalize(json.loads(SECTION_3_2_3_INPUT)).decode("utf-8")
        values = list(json.loads(out, object_pairs_hook=lambda pairs: pairs))
        self.assertEqual([v for _, v in values], SECTION_3_2_3_ORDER)


class CorpusValues(unittest.TestCase):
    """The value forms the corpus relies on (CTRL-04), stated directly."""

    def test_equivalent_number_forms_share_one_encoding(self):
        for text in ("3", "3.0", "3.00", "3e0", "30e-1", "0.3E1"):
            with self.subTest(text=text):
                self.assertEqual(canonicalize(json.loads(text)), b"3")

    def test_reordered_members_share_one_encoding(self):
        a = json.loads('{"service":"checkout","replicas":3}')
        b = json.loads('{"replicas":3.0,"service":"checkout"}')
        self.assertEqual(canonicalize(a), canonicalize(b))

    def test_sorted_compact_json_is_not_jcs(self):
        """The v0.1.2 encoder, kept here as the negative control for this file."""
        def old(o):
            return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        diverging = [3.0, 1e-7, 1e16, -0.0, json.loads(SECTION_3_2_3_INPUT)]
        for v in diverging:
            with self.subTest(v=v):
                self.assertNotEqual(old(v), canonicalize(v))

    def test_lone_surrogate_is_an_error(self):
        with self.assertRaises(ValueError):
            canonicalize(json.loads(r'"\udead"'))


if __name__ == "__main__":
    unittest.main()
