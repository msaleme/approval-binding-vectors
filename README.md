# Approval Binding Vectors (ABV) v0.1

A protocol-neutral conformance corpus for one question:

> **Does this record prove that what executed is what was approved?**

12 vectors — 9 negative, 3 positive controls — over six predicates. Dependency-free
reference checker. No protocol required.

```
$ python3 check.py
  PASS  CTRL-01      all six predicates hold
  PASS  CTRL-02      all six predicates hold
  PASS  CTRL-03      all six predicates hold
  PASS  NEG-P1-01    P1: approved action 'deploy.apply', executed 'deploy.destroy'
  PASS  NEG-P2-01    P2: executed arguments are not the approved arguments
  PASS  NEG-P2-02    P2: executed arguments are not the approved arguments
  PASS  NEG-P3-01    P3: referenced bytes at execution are not the approved bytes
  PASS  NEG-P3-02    P3: referenced bytes at execution are not the approved bytes
  PASS  NEG-P4-01    P4: executed at 2026-09-19T13:00:00Z after approval expired ...
  PASS  NEG-P5-01    P5: approval attested by the executing party (executor.example)
  PASS  NEG-P5-02    P5: no approval attestation
  PASS  NEG-P6-01    P6: approval nonce reused across 2 executions

12/12 vectors behaved as specified
acceptance controls: 3 accepted (a run with 0 is not a result, regardless of the negatives)
```

## Why the positive controls are the point

A checker that rejects everything passes every negative vector ever written. This is not a
hypothetical — it is what the corpus caught on its first adversarial run.

A deliberately weak checker was built to test whether the corpus discriminates. It compares
the reference string instead of dereferencing it, never checks who attested the approval,
and never checks expiry or reuse. Against the nine negative vectors it scored **9 of 9**:

```
naive checker MISSES 0: []
predicates it silently fails: []
false rejections of controls: 2
```

Nine out of nine, and it is not a binding at all. It rejects *anything containing a
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
| **P4** | The approval is **valid at the instant of execution**. |
| **P5** | The approval is attested by a party **distinct from the executor**. |
| **P6** | An approval authorizes **at most one** execution. |

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
generate.py          builds the vectors (each negative = a one-predicate mutation of a control)
check.py             dependency-free reference checker (first-failure verdict)
isolation.py         tests the corpus's own claim: exactly one predicate violated per vector
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

## Status

v0.1, 2026-09-19. Unreviewed by anyone other than its author — which, by its own argument,
is the thing that would make it worth something. If you implement a checker and disagree
with `check.py` on any vector, that disagreement is the most useful thing you can send back.
