#!/usr/bin/env python3
"""ABV isolation test — the claim the corpus makes about itself.

check.py reports the FIRST predicate a record fails, which is what a checker
should do but cannot demonstrate isolation: a vector that fails P1 and P4 looks
identical to one that fails only P1.

The corpus claims each negative vector violates EXACTLY its designated predicate
and satisfies the other five. That claim is what makes the decomposition a
contribution rather than a filing system, so it needs its own test.

This evaluates every predicate independently, with no short-circuit.
"""
from __future__ import annotations

import json
from pathlib import Path

import check as C


def p1(rec) -> bool:
    sc = rec["approval"]["scope"]
    return sc.get("action") is not None and all(
        e.get("action") == sc.get("action") for e in C_execs(rec))


def p2(rec) -> bool:
    """Arguments match, comparing the RESOLVED form but ignoring reference
    substitution failures (that is P3's job)."""
    sc = rec["approval"]["scope"]
    for e in C_execs(rec):
        try:
            if C.digest(C.resolve(e.get("arguments", {}))) != sc.get("arguments_digest"):
                # If the mismatch is attributable to references, P2 is not the
                # violated predicate.
                if _has_ref(e.get("arguments", {})):
                    continue
                return False
        except KeyError:
            continue
    return True


def p3(rec) -> bool:
    sc = rec["approval"]["scope"]
    for e in C_execs(rec):
        args = e.get("arguments", {})
        if not _has_ref(args):
            continue
        # committed the reference string rather than the bytes?
        if C.digest(args) == sc.get("arguments_digest"):
            return False
        try:
            if C.digest(C.resolve(args)) != sc.get("arguments_digest"):
                return False
        except KeyError:
            return False
    return True


def p4(rec) -> bool:
    # Fail-closed: no not_after, no execution time, or an unparseable time fails P4.
    # Until v0.1.3 a missing not_after returned True here (NEG-P4-02). Written out
    # rather than calling check.py, so the two implementations stay independent.
    ap = rec["approval"]
    if "not_after" not in ap:
        return False
    for e in C_execs(rec):
        if "at" not in e:
            return False
        try:
            if C.ts(e["at"]) > C.ts(ap["not_after"]):
                return False
        except (TypeError, ValueError):
            return False
    return True


def p5(rec) -> bool:
    atts = [a for a in rec.get("attestations", []) if a.get("claim") == "approval"]
    if not atts:
        return False
    executors = {e.get("by") for e in C_execs(rec)}
    import hmac, hashlib
    for a in atts:
        auth = a.get("authority")
        if auth in executors or auth not in C.KEYS:
            return False
        expected = hmac.new(C.KEYS[auth], C.jcs(rec["approval"]["scope"]), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, a.get("mac", "")):
            return False
    return True


def p6(rec) -> bool:
    # At most one execution per approval, regardless of nonce values (see check.py).
    return len(C_execs(rec)) < 2


def _has_ref(args) -> bool:
    return any(isinstance(v, dict) and "$ref" in v for v in args.values())


def C_execs(rec):
    ex = rec["execution"]
    return ex if isinstance(ex, list) else [ex]


PREDICATES = {"P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "P6": p6}


def main() -> int:
    vectors = sorted((Path(__file__).parent / "vectors").glob("*.json"))
    bad = 0
    print(f"{'vector':<12} {'designated':<11} " + " ".join(f"{k:<4}" for k in PREDICATES) + "  isolated?")
    for v in vectors:
        rec = json.loads(v.read_text())
        results = {k: f(rec) for k, f in PREDICATES.items()}
        designated = rec.get("negates")
        failing = {k for k, ok in results.items() if not ok}
        if designated is None:
            isolated = not failing
            verdict = "all hold" if isolated else f"CONTROL FAILS {sorted(failing)}"
        else:
            isolated = failing == {designated}
            verdict = "exactly one" if isolated else f"NOT ISOLATED: fails {sorted(failing)}"
        bad += not isolated
        cells = " ".join(("ok  " if results[k] else "FAIL") for k in PREDICATES)
        print(f"  {v.stem:<12} {str(designated or '—'):<11} {cells}  {verdict}")

    print()
    if bad:
        print(f"ISOLATION BROKEN in {bad} vector(s) — the decomposition claim does not hold.")
        return 1
    print("Isolation holds: every negative violates exactly its designated predicate "
          "and satisfies the other five; every control satisfies all six.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
