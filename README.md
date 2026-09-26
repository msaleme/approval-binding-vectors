# Approval Binding Vectors (ABV) v0.1

A protocol-neutral conformance corpus for one question:

> **Does this record prove that what executed is what was approved?**

15 vectors — 11 negative, 4 positive controls — over six predicates. Dependency-free
reference checker with an RFC 8785 canonicalizer. No protocol required.

```
$ python3 check.py
  PASS  CTRL-01      all six predicates hold
  PASS  CTRL-02      all six predicates hold
  PASS  CTRL-03      all six predicates hold
  PASS  CTRL-04      all six predicates hold
  PASS  NEG-P1-01    P1: approved action 'deploy.apply', executed 'deploy.destroy'
  PASS  NEG-P2-01    P2: executed arguments are not the approved arguments
  PASS  NEG-P2-02    P2: executed arguments are not the approved arguments
  PASS  NEG-P3-01    P3: referenced bytes at execution are not the approved bytes
  PASS  NEG-P3-02    P3: referenced bytes at execution are not the approved bytes
  PASS  NEG-P4-01    P4: executed at 2026-09-19T13:00:00Z after approval expired ...
  PASS  NEG-P4-02    P4: approval carries no not_after; ABV approvals are time-bounded
  PASS  NEG-P5-01    P5: approval attested by the executing party (executor.example)
  PASS  NEG-P5-02    P5: no approval attestation
  PASS  NEG-P6-01    P6: one approval, 2 executions
  PASS  NEG-P6-02    P6: one approval, 2 executions

15/15 vectors behaved as specified
acceptance controls: 4 accepted (a run with 0 is not a result, regardless of the negatives)
```

## Why the positive controls are the point

A checker that rejects everything passes every negative vector ever written. This is not a
hypothetical — it is what the corpus caught on its first adversarial run.

A deliberately weak checker was built to test whether the corpus discriminates. It compares
the reference string instead of dereferencing it, never checks who attested the approval,
and never checks expiry or reuse. Against the eleven negative vectors it scored **11 of 11**:

```
naive checker MISSES 0: []
predicates it silently fails: []
false rejections of controls: 2
```

Ten out of ten, and it is not a binding at all. It rejects *anything containing a
reference*, which happens to include every negative vector — and also `CTRL-01` and
`CTRL-02`. The controls are the only thing in the corpus that can tell the difference
between a checker that works and a checker that refuses.

**Report `CTRL` results or do not report results.** A submission carrying negative passes
without control passes is not a result.

## The isolation claim, and its test

The corpus claims each negative vector violates **exactly** its designated predicate and
satisfies the other five. `check.py` cannot demonstrate that — it reports the first failure,
which is what a checker should do and which makes a vector failing P1-and-P4 look identical
to one failing only P1. `isolation.py` evaluates all six independently, with no short-circuit:

```
$ python3 isolation.py
  vector       designated  P1   P2   P3   P4   P5   P6    isolated?
  CTRL-01      —           ok   ok   ok   ok   ok   ok    all hold
  NEG-P1-01    P1          FAIL ok   ok   ok   ok   ok    exactly one
  NEG-P4-01    P4          ok   ok   ok   FAIL ok   ok    exactly one
  ...
  Isolation holds: every negative violates exactly its designated predicate
  and satisfies the other five; every control satisfies all six.
```

A verdict can be correct while the decomposition is wrong, and the decomposition is the
contribution. **A counterexample to isolation is a break even if the overall verdict stands.**

## The six predicates

| ID | Predicate |
|---|---|
| **P1** | The approval's scope commits to the executed **action**. |
| **P2** | The approval's scope commits to the executed **argument bytes**. |
| **P3** | Where content is named by **reference**, the commitment covers the dereferenced bytes, and the executor verifies and then consumes those same bytes. |
| **P4** | The approval carries an expiry and has **not expired** at the recorded execution time; no expiry fails P4. **Expiry only**: v0.1 does not model revocation. |
| **P5** | A **separate attester**: an approval attestation exists, its attester is not an executor, its key is known, and it verifies over the scope. Does **not** test authority for the scope. |
| **P6** | An approval authorises **at most one** execution, whatever nonce each execution claims — a *profile choice*; reusable approvals can be legitimate. |

Full definitions, canonical form, and the P2/P3 precedence rule: [`SPEC.md`](SPEC.md).
Real-world referent for every predicate: [`profiles/OBSERVED.md`](profiles/OBSERVED.md).

## What this is not

- **Not a protocol.** It defines no wire format anyone is asked to adopt.
- **Not a security rating.** It tests a record, not a deployment. A sound record checked by
  the party it constrains proves nothing; the enforcement boundary is an architectural
  property this corpus cannot see.
- **Not a judgement on the protocols it cites.** Each referent is reported at its own
  weight, and a gap that is a *declared scope decision* is recorded as a decision.
- **Not validated by its own reference checker.** `check.py` demonstrates the vector set is
  satisfiable. An implementation that disagrees with it is a result worth reporting, not an
  error.

## Layout

```
SPEC.md              predicates, canonical form, verdicts, acceptance controls
jcs.py               RFC 8785 canonicalizer, shared by the generator and every checker
generate.py          builds the vectors (each negative = a one-predicate mutation of a control)
check.py             dependency-free reference checker (first-failure verdict)
isolation.py         tests the corpus's own claim: exactly one predicate violated per vector
test_jcs.py          jcs.py against the values RFC 8785 publishes (python3 -m unittest)
test_check.py        missing members fail closed, in check.py and isolation.py alike
vectors/*.json       the corpus
profiles/OBSERVED.md where each predicate was observed in a real specification
```

Vectors are **generated, not hand-written**, so that every negative is provably a
single-predicate mutation of a passing control. Hand-written negatives drift into failing
for two reasons at once, which makes a checker look correct when it is only rejecting a file.

## Licence

**MIT.** Deliberately permissive, because the point of a vector corpus is that other
implementations copy the fixtures into their own test suites. A corpus nobody can legally
vendor is a corpus nobody will reproduce.

## Standing reproduction challenge

A published, commit-pinned invitation to disagree with this corpus — what counts as a break,
what a reproduction report needs, and what will and will not be claimed about your result:
**[CHALLENGE.md](CHALLENGE.md)**.

Short version: a reproducible disagreement with `check.py` or `isolation.py` is the single most
useful thing you can send back. Negative-vector agreement alone is insufficient evidence of
checker correctness — report `CTRL` results or do not report results.

## Changelog

- **v0.1.3** (2026-09-26). **Corrections: canonical form, a near-miss control that tests it,
  and fail-open expiry.**
  - **Canonicalization was not RFC 8785.** SPEC has always said digests are over JCS
    (RFC 8785); `check.py` and `generate.py` used `json.dumps(sort_keys=True)`, which emits
    `3.0` where RFC 8785 emits `3`. A record executing `replicas: 3.0` against an approval
    over `3` was therefore rejected P2: a false reject under the corpus's own rules. New
    `jcs.py` implements RFC 8785 and is the only canonicalizer in the repository;
    `test_jcs.py` checks it against RFC 8785 Appendix B and the section 3.2 worked example.
    The thirteen existing vectors never contained a value on which the two encodings differ,
    so they are **byte-identical** and every published digest stands.
  - **`CTRL-02` did not test what SPEC said it tested.** SPEC described it as covering "a
    re-ordered object, a different but equivalent number form". It re-orders only the
    approval object, which is never hashed, and contains no number form. New positive
    control **CTRL-04** puts an equivalent number form inside the digested arguments. The
    v0.1.2 checker scores it `FAIL expected accept, got reject`.
  - **A missing `not_after` was accepted.** `check.py` and `isolation.py` skipped P4 when the
    approval carried no expiry. P4 now fails closed, as P5 already did for a missing
    attestation, and SPEC says ABV approvals are time-bounded. New negative **NEG-P4-02**
    (no `not_after`); the v0.1.2 checker accepts it. Two neighbours of the same class also
    fail closed now, covered by `test_check.py` rather than new vectors: a missing or
    unparseable execution time fails P4 (previously an uncaught exception, neither
    verdict), and a scope with no action fails P1 (previously accepted when the execution
    also had none).
  - `CHALLENGE.md` re-pinned (it still pinned `88548a6`, which predates the v0.1.2 P6 fix).
  - Found by the author's own review of the corpus, not by an outside reviewer. The
    canonicalization defect is the same class an outside reviewer, VrtxOmega, found in the
    Agent Security Harness RCL fixtures in July: a fixture labelled JCS that was sorted
    compact JSON ([harness #304](https://github.com/msaleme/red-team-blue-team-agent-fabric/issues/304)).
    That fix narrowed the label; this one implements the standard the label names.
- **v0.1.2** (2026-09-23). **P6 fix.** `check.py` and `isolation.py` implemented P6 as "no two
  executions share a `nonce_used` value", so one approval executed twice under *distinct*
  nonce values was accepted, although P6 says an approval authorises at most one execution.
  Both now reject more than one execution per approval. New negative **NEG-P6-02** (same
  approval, distinct nonces) catches the old behaviour: the v0.1.1 checker scores it
  `FAIL expected reject, got accept`. The twelve existing vectors are byte-identical. P4 is
  now described as expiry-only, which is what the checker has always tested. Found by an
  external review of the accompanying paper, which asked whether P6 detects reuse of an
  approval or only duplication of a nonce.
- **v0.1.1** (2026-09-19). P5 described as a separate-attester check, not an authority check.
- **v0.1.0** (2026-09-19). Initial release.

## Status

v0.1, 2026-09-19. Unreviewed by anyone other than its author — which, by its own argument,
is the thing that would make it worth something. If you implement a checker and disagree
with `check.py` on any vector, that disagreement is the most useful thing you can send back.
