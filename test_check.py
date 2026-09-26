#!/usr/bin/env python3
"""Missing members fail closed, in check.py and isolation.py alike.

Each case removes one member from CTRL-01 and asserts both implementations
attribute the failure to the same single predicate. v0.1.0 to v0.1.2 accepted
the first case and the last, and raised KeyError on the second.

    python3 -m unittest test_check -v
"""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import check
import isolation

CTRL_01 = json.loads((Path(__file__).parent / "vectors" / "CTRL-01.json").read_text())


def verdict(rec):
    try:
        return check.verify(rec)[:2]
    except check.Reject as r:
        return ("reject", r.predicate)


def failing(rec):
    return {k for k, f in isolation.PREDICATES.items() if not f(rec)}


class MissingMembers(unittest.TestCase):
    def assertOnly(self, rec, predicate):
        self.assertEqual(verdict(rec), ("reject", predicate))
        self.assertEqual(failing(rec), {predicate})

    def test_control_is_accepted(self):
        self.assertEqual(verdict(CTRL_01), ("accept", None))
        self.assertEqual(failing(CTRL_01), set())

    def test_no_not_after_fails_p4(self):
        rec = copy.deepcopy(CTRL_01)
        del rec["approval"]["not_after"]
        self.assertOnly(rec, "P4")

    def test_no_execution_time_fails_p4(self):
        rec = copy.deepcopy(CTRL_01)
        del rec["execution"]["at"]
        self.assertOnly(rec, "P4")

    def test_unparseable_time_fails_p4(self):
        rec = copy.deepcopy(CTRL_01)
        rec["execution"]["at"] = "yesterday"
        self.assertOnly(rec, "P4")

    def test_no_action_on_either_side_fails_p1(self):
        rec = copy.deepcopy(CTRL_01)
        del rec["approval"]["scope"]["action"]
        del rec["execution"]["action"]
        # Re-attest the altered scope so P5 still holds and only P1 is in question.
        import hashlib, hmac
        rec["attestations"][0]["mac"] = hmac.new(
            check.KEYS["approver.example"], check.jcs(rec["approval"]["scope"]), hashlib.sha256
        ).hexdigest()
        self.assertOnly(rec, "P1")


if __name__ == "__main__":
    unittest.main()
