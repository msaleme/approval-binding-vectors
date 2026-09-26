#!/usr/bin/env python3
"""Generate the ABV v0.1 vector set.

Vectors are generated rather than hand-written so that every negative case is
provably a one-predicate mutation of a passing control: each is built by taking
a sound record and breaking exactly one thing. Hand-written negatives drift into
failing for two reasons at once, which makes a checker look correct when it is
only rejecting the file.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

OUT = Path(__file__).parent / "vectors"

# Keyed digests stand in for signatures. Two distinct keys model two parties;
# a verifier is assumed to hold only the approver's key.
KEYS = {
    "approver.example": b"abv/approver",
    "executor.example": b"abv/executor",
}

# A content store, so a reference can be dereferenced (and can change).
BLOBS = {
    "blob://plan-v1": b'{"target":"prod","replicas":3}',
    "blob://plan-v2": b'{"target":"prod","replicas":300}',
}


# The same RFC 8785 canonicalizer check.py uses; one implementation, so the digests
# the vectors carry cannot drift from the digests the checker recomputes.
from jcs import canonicalize as jcs


def digest(obj) -> str:
    return hashlib.sha256(jcs(obj)).hexdigest()


def blob_digest(uri: str) -> str:
    return hashlib.sha256(BLOBS[uri]).hexdigest()


def mac(authority: str, obj) -> str:
    return hmac.new(KEYS[authority], jcs(obj), hashlib.sha256).hexdigest()


def attest(authority: str, claim: str, scope) -> dict:
    return {"claim": claim, "authority": authority, "mac": mac(authority, scope)}


def sound(**over) -> dict:
    """A record satisfying all six predicates. Every vector starts here."""
    action = "deploy.apply"
    arguments = {"manifest": {"$ref": "blob://plan-v1"}, "confirm": True}
    args_digest = digest({"manifest": blob_digest("blob://plan-v1"), "confirm": True})
    scope = {"action": action, "arguments_digest": args_digest}
    rec = {
        "abv": "0.1",
        "request": {"action": action, "arguments": arguments},
        "approval": {
            "scope": scope,
            "authority": "approver.example",
            "not_after": "2026-09-19T12:00:00Z",
            "nonce": "n-0001",
        },
        "execution": {
            "action": action,
            "arguments": arguments,
            "at": "2026-09-19T11:00:00Z",
            "status": "completed",
            "by": "executor.example",
            "nonce_used": "n-0001",
        },
        "attestations": [attest("approver.example", "approval", scope)],
    }
    for k, v in over.items():
        rec[k] = v
    return rec


def emit(vid: str, negates: str | None, rec: dict, note: str) -> None:
    rec = dict(rec)
    rec["id"] = vid
    rec["note"] = note
    if negates:
        rec["negates"] = negates
        rec["expect"] = {"verdict": "reject", "predicate": negates}
    else:
        rec["expect"] = {"verdict": "accept"}
    ordered = {k: rec[k] for k in
               ["abv", "id", "negates", "note", "request", "approval", "execution",
                "attestations", "expect"] if k in rec}
    (OUT / f"{vid}.json").write_text(json.dumps(ordered, indent=2) + "\n")


def build() -> None:
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.json"):
        f.unlink()

    # ---------- positive controls ----------
    emit("CTRL-01", None, sound(),
         "Fully sound record. A checker that cannot accept this has not implemented a "
         "binding; it has implemented a refusal.")

    # near-miss: same record, members of the (unhashed) approval object reordered.
    # Any JSON parser erases this; CTRL-04 is the near miss inside hashed content.
    nm = sound()
    nm["approval"] = {k: nm["approval"][k] for k in reversed(list(nm["approval"]))}
    emit("CTRL-02", None, nm,
         "Byte-level near miss: identical content, object members emitted in a different "
         "order. Canonicalization must make this indistinguishable from CTRL-01.")

    # a second, differently-shaped sound record: inline arguments, no reference.
    inline_args = {"path": "/etc/app.conf", "mode": "0644"}
    ia_scope = {"action": "fs.write", "arguments_digest": digest(inline_args)}
    emit("CTRL-03", None, sound(
        request={"action": "fs.write", "arguments": inline_args},
        approval={"scope": ia_scope, "authority": "approver.example",
                  "not_after": "2026-09-19T12:00:00Z", "nonce": "n-0002"},
        execution={"action": "fs.write", "arguments": inline_args,
                   "at": "2026-09-19T11:00:00Z", "status": "completed",
                   "by": "executor.example", "nonce_used": "n-0002"},
        attestations=[attest("approver.example", "approval", ia_scope)]),
        "Sound record with inline arguments and no reference, so P3 is vacuous. Guards "
        "against a checker that only works when a $ref is present.")

    # near-miss inside the digested arguments: an equivalent number form. The
    # approval commits replicas=3; the execution carries 3.0. RFC 8785 serialises
    # both as 3. Sorted compact JSON (v0.1.0 to v0.1.2) emits 3.0 and rejects P2.
    nf_args = {"service": "checkout", "replicas": 3}
    nf_scope = {"action": "deploy.scale", "arguments_digest": digest(nf_args)}
    emit("CTRL-04", None, sound(
        request={"action": "deploy.scale", "arguments": nf_args},
        approval={"scope": nf_scope, "authority": "approver.example",
                  "not_after": "2026-09-19T12:00:00Z", "nonce": "n-0005"},
        execution={"action": "deploy.scale", "arguments": {"service": "checkout", "replicas": 3.0},
                   "at": "2026-09-19T11:00:00Z", "status": "completed",
                   "by": "executor.example", "nonce_used": "n-0005"},
        attestations=[attest("approver.example", "approval", nf_scope)]),
        "Near miss inside hashed content: approval over replicas 3, execution carries 3.0. "
        "RFC 8785 serialises both as 3, so the digests match. A checker that rejects this "
        "is not canonicalising numbers per RFC 8785.")

    # ---------- P1: action ----------
    r = sound()
    r["execution"]["action"] = "deploy.destroy"
    emit("NEG-P1-01", "P1", r,
         "Approval scopes deploy.apply; deploy.destroy executed. Arguments match.")

    # ---------- P2: arguments ----------
    # P2 vectors carry NO reference. When an argument is by reference, an
    # argument change is also a dereference change and the two predicates
    # overlap; P3 is then the more specific diagnosis (see SPEC "Precedence").
    # Keeping P2 inline is what makes the two independently testable.
    def inline(action, args, nonce):
        sc = {"action": action, "arguments_digest": digest(args)}
        return sound(
            request={"action": action, "arguments": args},
            approval={"scope": sc, "authority": "approver.example",
                      "not_after": "2026-09-19T12:00:00Z", "nonce": nonce},
            execution={"action": action, "arguments": args, "at": "2026-09-19T11:00:00Z",
                       "status": "completed", "by": "executor.example", "nonce_used": nonce},
            attestations=[attest("approver.example", "approval", sc)])

    r = inline("deploy.scale", {"service": "checkout", "replicas": 3}, "n-0003")
    r["execution"]["arguments"] = {"service": "checkout", "replicas": 300}
    emit("NEG-P2-01", "P2", r,
         "Same action, inline arguments, one numeric value differs: 3 replicas approved, "
         "300 executed. No reference involved, so this is unambiguously P2.")

    r = inline("fs.write", {"path": "/etc/app.conf", "mode": "0644"}, "n-0004")
    r["execution"]["arguments"] = {"path": "/etc/shadow", "mode": "0644"}
    emit("NEG-P2-02", "P2", r,
         "One string argument differs. Catches a checker comparing the action and a subset "
         "of arguments rather than a digest over all of them.")

    # ---------- P3: dereference ----------
    # The reference is unchanged; the BYTES behind it are not the ones approved.
    r = sound()
    approved_args_digest = digest({"manifest": blob_digest("blob://plan-v1"), "confirm": True})
    r["approval"]["scope"] = {"action": "deploy.apply", "arguments_digest": approved_args_digest}
    r["attestations"] = [attest("approver.example", "approval", r["approval"]["scope"])]
    r["execution"]["arguments"] = {"manifest": {"$ref": "blob://plan-v2"}, "confirm": True}
    r["execution"]["dereferenced"] = {"blob://plan-v2": blob_digest("blob://plan-v2")}
    emit("NEG-P3-01", "P3", r,
         "The approval commits dereferenced bytes; execution dereferences a different blob. "
         "A checker comparing only the reference STRING accepts this.")

    # Commitment over the reference string rather than its bytes.
    r = sound()
    weak_digest = digest({"manifest": "blob://plan-v1", "confirm": True})
    r["approval"]["scope"] = {"action": "deploy.apply", "arguments_digest": weak_digest}
    r["attestations"] = [attest("approver.example", "approval", r["approval"]["scope"])]
    r["execution"]["arguments"] = {"manifest": {"$ref": "blob://plan-v2"}, "confirm": True}
    emit("NEG-P3-02", "P3", r,
         "The approval committed the reference as a string, leaving the referenced bytes "
         "unbound. This is the PACT -00 harness_uri failure in neutral form.")

    # ---------- P4: freshness ----------
    r = sound()
    r["execution"]["at"] = "2026-09-19T13:00:00Z"   # after not_after
    emit("NEG-P4-01", "P4", r,
         "Correctly scoped and attested approval, executed after it expired.")

    r = sound()
    del r["approval"]["not_after"]
    emit("NEG-P4-02", "P4", r,
         "Correctly scoped and attested approval with no not_after. ABV approvals are "
         "time-bounded; freshness cannot be established, so P4 fails closed. A checker "
         "that skips expiry when the member is absent accepts this.")

    # ---------- P5: authority ----------
    r = sound()
    r["attestations"] = [attest("executor.example", "approval", r["approval"]["scope"])]
    r["approval"]["authority"] = "executor.example"
    emit("NEG-P5-01", "P5", r,
         "The executing party is the only attester of its own approval. Every other "
         "predicate holds.")

    r = sound()
    r["attestations"] = []
    emit("NEG-P5-02", "P5", r,
         "No attestation at all. The record asserts an approval that nothing witnesses.")

    # ---------- P6: single use ----------
    r = sound()
    r["execution"] = [
        dict(r["execution"]),
        dict(r["execution"], at="2026-09-19T11:30:00Z"),
    ]
    emit("NEG-P6-01", "P6", r,
         "One approval, one nonce, two executions.")

    r = sound()
    r["execution"] = [
        dict(r["execution"]),
        dict(r["execution"], at="2026-09-19T11:30:00Z", nonce_used="n-0002"),
    ]
    emit("NEG-P6-02", "P6", r,
         "One approval, two executions under distinct nonce values. A checker that only "
         "compares nonces for duplicates accepts this; the approval was still used twice.")

    print(f"wrote {len(list(OUT.glob('*.json')))} vectors")


if __name__ == "__main__":
    build()
