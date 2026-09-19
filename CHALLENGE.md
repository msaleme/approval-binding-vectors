# Standing Reproduction Challenge

> Accompanies *From Approval to Execution: Assurance Boundaries in Three Agent Protocols*,
> [10.5281/zenodo.22847475](https://doi.org/10.5281/zenodo.22847475). Every reviewer of that
> paper closed with the same sentence: they had not independently reproduced these results.
> This page exists so that someone can.

**Status:** open, no end date · **Version:** 1.0, 2026-09-19

Two people have independently reproduced or challenged work in this portfolio without being
asked. Both times the exchange was worth more than anything published in the same period,
and both times it happened by luck. This is the standing version, so it stops depending on
luck.

## What is being offered

Two corpora, pinned, with the verdicts they are claimed to produce. You are invited to build
your own checker and disagree.

| Corpus | Claim under challenge | Where to start |
|---|---|---|
| **ABV** — approval binding vectors, 12 vectors over 6 predicates | (a) each negative vector violates **exactly** its designated predicate and satisfies the other five; (b) every positive control is accepted under the published rules. | [`msaleme/approval-binding-vectors`](https://github.com/msaleme/approval-binding-vectors) @ [`88548a61c960`](https://github.com/msaleme/approval-binding-vectors/tree/88548a61c960d2ddd25ded9d9a0eceedd4455c83) · rules [`SPEC.md`](https://github.com/msaleme/approval-binding-vectors/blob/88548a61c960d2ddd25ded9d9a0eceedd4455c83/SPEC.md) · vectors [`vectors/`](https://github.com/msaleme/approval-binding-vectors/tree/88548a61c960d2ddd25ded9d9a0eceedd4455c83/vectors) (each carries its own `expect`) · checkers [`check.py`](https://github.com/msaleme/approval-binding-vectors/blob/88548a61c960d2ddd25ded9d9a0eceedd4455c83/check.py), [`isolation.py`](https://github.com/msaleme/approval-binding-vectors/blob/88548a61c960d2ddd25ded9d9a0eceedd4455c83/isolation.py) · digests [`SHA256SUMS`](https://github.com/msaleme/approval-binding-vectors/blob/88548a61c960d2ddd25ded9d9a0eceedd4455c83/SHA256SUMS) |
| **RCL** — receipt claim-level verification, 11 vectors | A format-valid, correctly-signed receipt can still be claim-invalid, and a claim-level verifier must reject it on semantic grounds while envelope-signature verification succeeds. | [`msaleme/red-team-blue-team-agent-fabric`](https://github.com/msaleme/red-team-blue-team-agent-fabric) @ [`e2a647fa4976`](https://github.com/msaleme/red-team-blue-team-agent-fabric/tree/e2a647fa49760cd290e3b9541751ab5e357ad568) · **acceptance rules and vector definitions**: [`protocol_tests/receipt_claim_harness.py`](https://github.com/msaleme/red-team-blue-team-agent-fabric/blob/e2a647fa49760cd290e3b9541751ab5e357ad568/protocol_tests/receipt_claim_harness.py) — `ClaimLevelVerifier.verify()` is the normative rule set, the `NEGATIVES` table names each vector, and `RCL-008` is the acceptance control · IDs and line anchors in [`HARNESS_TEST_CATALOG.md`](https://github.com/msaleme/red-team-blue-team-agent-fabric/blob/e2a647fa49760cd290e3b9541751ab5e357ad568/HARNESS_TEST_CATALOG.md) · run `python3 -m protocol_tests.receipt_claim_harness --simulate` |

Submissions go to the issue tracker of the corpus you ran against.

## What counts as a break

Ranked by how much it would change what I do. All five are real outcomes and I will publish
any of them.

A corpus does not accept or reject anything: **checkers produce verdicts, and fixtures carry
expected verdicts**. Both are fair game — you may challenge the reference checker's
behaviour, a fixture's expected label, or both. "Correct" below means *correct under the
published rules* (`SPEC.md` for ABV; the suite's stated claim for RCL), not under your own
threat model, though an argument that the rules are the wrong rules is also welcome and
should say that is what it is.

1. **A false accept.** A record the published rules require to be rejected, for which the
   reference checker returns accept — or a fixture labelled `accept` that the rules require
   to be rejected. The dangerous direction and the most valuable thing you can find.
2. **A false reject.** The same in the other direction. Less alarming and more corrosive: a
   checker that rejects a legitimate case is one that gets switched off, and then nothing is
   checked at all.
3. **A wrong reason.** A checker attributes a rejection to a predicate that the vector
   satisfies under the published rules. This challenges the **checker's diagnostic
   correctness** — the reference checker's or your own, and finding out which is the point.
   If the fixture turns out to violate a predicate other than its designated one, that is
   item 5 instead.
4. **A canonicalisation disagreement.** Your implementation computes a different digest than
   mine over records the published rules define as equivalent — same covered members, same
   declared canonical form, differing only in serialisation the rules say is immaterial. A
   disagreement may expose an implementation error on either side, or an ambiguity in the
   rules. **If the published rules leave the choice unresolved, that is a specification
   defect**; if they resolve it, one of us is simply wrong, and finding out which is still
   worth the exchange.

5. **A broken isolation claim (ABV only).** A negative vector whose actual set of violated
   predicates differs from the single designated one — whether it violates **none**, a
   different one, or more than one. The overall verdict can stay correct while the
   decomposition is wrong, and the decomposition is the contribution. This is why full
   reports need **per-predicate results**, not just final verdicts. [`isolation.py`](https://github.com/msaleme/approval-binding-vectors/blob/88548a61c960d2ddd25ded9d9a0eceedd4455c83/isolation.py)
   is my own test of this claim. A reproducible disagreement with it is a **finding to
   investigate** — either implementation could be wrong. A demonstrated mismatch between its
   results and the published predicate definitions in `SPEC.md` is a **break**.

## What counts as a reproduction

Borrowing the standard from the party who set it, because it is the right one:
**implementation separation, not source blindness.** Read the source freely. Write your own
checker. Reuse of the reference implementation is not a reproduction of it.

**A complete reproduction report** includes: the pin you ran against by commit and artifact
digest; your verdict for **every** vector, not only the disagreements; **per-predicate**
results where the corpus defines predicates; and your positive-control results.

**A partial finding** may concern a single vector. Say what you tested and include enough to
reproduce the disagreement. A valid isolated counterexample is welcome and is not diminished
by being partial.

**Negative-vector agreement alone is insufficient evidence of checker correctness.** A
checker that rejects everything matches the expected rejection verdict for every negative
vector in both corpora. That is not
hypothetical: a deliberately weak checker built against ABV v0.1 — one that compares the
reference string instead of dereferencing it, and never checks attestation, expiry or reuse
— scored **nine out of nine** on the negatives while being no binding at all ([`weak_checker_demo.py`](https://github.com/msaleme/approval-binding-vectors/blob/88548a61c960d2ddd25ded9d9a0eceedd4455c83/weak_checker_demo.py), recorded output in [`WEAK_CHECKER_RESULT.txt`](https://github.com/msaleme/approval-binding-vectors/blob/88548a61c960d2ddd25ded9d9a0eceedd4455c83/WEAK_CHECKER_RESULT.txt)). It rejected
anything containing a reference, which the positive controls caught and the negatives could
not.

**"The same logical record"** means two serialisations that the published canonical-form
rules define as equivalent: identical covered members with identical values, differing only
in ordering or encoding those rules declare immaterial. If you think two records are
equivalent and the rules do not say so, that disagreement is itself finding 4.

## What I will not claim

This is the part that makes the rest mean anything.

- **If nobody breaks it, I will not call it validated.** Absence of a submitted break is
  absence of evidence. It is not a pass, and I will not cite it as one.
- **If you break it, that is the result**, and it gets published with your finding and your
  name if you want it, at the pin you used, whether or not the fix is ready.
- **A reproduction that agrees with me is not validation of my instrument.** Independent
  agreement supports the *reproducibility of the reported verdicts on the tested vectors*.
  It does not establish that the specification is correct, that the corpus is sufficient, or
  that either checker handles untested cases correctly — two implementations can share the
  same mistaken reading, and a corpus cannot certify itself.
- **I will not claim your work as an endorsement**, will not describe you as a reviewer or
  partner, and will not use your name in any promotional context. If you would rather not be
  named at all, say so and the finding publishes anonymously.

## What is not being asked

No endorsement, no certification, no broad review, no co-authorship, and nothing that
requires you to adopt anything. One vector checked and disagreed with is a complete and
welcome contribution.

## Scope and authorization

- **This challenge invites local, offline testing of the published fixtures and checkers. It
  grants no authorization to test live systems or deployed services** — mine, my employer's,
  or any third party's. Both corpora are pure data and both reference checkers run offline
  with no network access and no dependencies, so participation never requires touching
  anything that is not in the repository you cloned.
- The challenge covers the published fixtures and reference checkers, **including new
  offline counterexamples you construct and evaluate under the pinned rules** — false
  accepts and false rejects invite exactly that. It is not an invitation to test any
  deployed service, any employer's systems, or any third party named in the reference
  material.
- Where a corpus cites another project's specification as a referent, that citation is
  descriptive. Those projects are not party to this challenge and nothing here is a claim
  about their security.

## How to submit

Open an issue on the corpus you ran against, titled `reproduction:` followed by the pin.
Disagreements are more useful than agreements, and partial runs are more useful than
nothing.

---

*Views my own, not my employer's.*
