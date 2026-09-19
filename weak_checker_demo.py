#!/usr/bin/env python3
"""A DELIBERATELY WEAK checker, used only to prove the corpus discriminates.

It makes the three mistakes the corpus exists to catch:
  1. compares the reference STRING instead of dereferencing  (should miss P3)
  2. never checks who attested the approval                   (should miss P5)
  3. never checks expiry or reuse                             (should miss P4, P6)
It does compare action and arguments, so it should still catch P1 and P2.
"""
import hashlib, json, sys
from pathlib import Path

def jcs(o): return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
def dg(o): return hashlib.sha256(jcs(o)).hexdigest()

rows = []
for v in sorted((Path(sys.argv[1])).glob("*.json")):
    rec = json.loads(v.read_text())
    ex = rec["execution"]
    ex = ex[0] if isinstance(ex, list) else ex
    sc = rec["approval"]["scope"]
    verdict = "accept"
    if ex.get("action") != sc.get("action"):
        verdict = "reject"
    elif dg(ex.get("arguments", {})) != sc.get("arguments_digest"):
        verdict = "reject"
    want = rec["expect"]["verdict"]
    rows.append((v.stem, want, verdict, rec.get("negates")))

missed = [r for r in rows if r[1] == "reject" and r[2] == "accept"]
wrong  = [r for r in rows if r[1] == "accept" and r[2] == "reject"]
print(f"{'vector':<12} {'expected':<9} {'naive says':<11} caught?")
for stem, want, got, neg in rows:
    ok = "yes" if want == got else ("MISSED" if want == "reject" else "false-reject")
    print(f"  {stem:<12} {want:<9} {got:<11} {ok}")
print(f"\nnaive checker MISSES {len(missed)}: {[m[0] for m in missed]}")
print(f"predicates it silently fails: {sorted({m[3] for m in missed})}")
print(f"false rejections of controls: {len(wrong)}")
