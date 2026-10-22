# Verifiable Intent reference verifier: adversarial probe (2026-10-22)

An offline probe of the Verifiable Intent (VI) reference verifier, run against its own security-model §4 attack list. It is **not a defect report**. Every accepted case is a check the spec assigns to the integrator, to the payment network, or to whichever party holds both halves of the credential.

## Setup

- **Target:** `agent-intent/verifiable-intent` at `356c296` (v0.1.0, Apache-2.0; spec and reference implementation). Its maintainer commits from a mastercard.com address.
- **Environment:** isolated venv (Python 3.15.0, cryptography 50.0.2). The repo's own suite passes: **326 passed**.
- **Method:** `probe.py` builds a valid autonomous (three-layer) chain with the library's own issuance API, changes one thing per case (following security-model §4), and records `verify_chain` and, where relevant, `check_constraints`. Raw output: `results.json`. The case numbers below follow the table; `results.json` labels them by spec section.
- **Two call profiles:**
  - **default:** the call shape the repo's own integration tests use (issuer key plus serialized layers, no expected aud or nonce).
  - **hardened:** default plus `expected_l2_*` and `expected_l3_*` aud and nonce.

## Reproduce

```bash
git clone https://github.com/agent-intent/verifiable-intent.git vi && git -C vi checkout 356c296
python3 -m venv .venv && .venv/bin/pip install ./vi pytest
(cd vi && ../.venv/bin/python -m pytest -q)        # expect: 326 passed
.venv/bin/python probe.py vi > results.json        # one row per case
```

Run with Python 3.15.0 and cryptography 50.0.2. `probe.py` takes the path to the checkout and imports the repo's `examples/helpers.py` (fixed test keys and fixtures). Nothing touches the network.

**Clock skew (cases 9 and 10).** Here the L3a was issued 400 s ago and expired 200 s ago. With the library's default `clock_skew_seconds=300`, `verify_chain` accepts it. The spec gives 300 s as RECOMMENDED, so this is by design: the tolerance turns a 5-minute L3 into a usable window of up to about 15 minutes. With `clock_skew_seconds=60` it is rejected ("L3a (payment) expired at ...").

**Coverage.** Seven of the nine §4 categories were exercised: 4.1, 4.2, 4.3 (modelled as an L2 re-signed by another key, since a stripped constraint cannot be re-signed without the user key), 4.4 (both views plus each partial view), 4.5, 4.6 and 4.9. Not exercised: 4.7 disclosure withholding and 4.8 type confusion.

## Results

| # | Case (VI §) | Spec expectation | default | hardened | Reading |
|---|---|---|---|---|---|
| P0 | valid chain (positive control) | accept | valid | valid | Control holds. Default reports `l2_aud`, `l2_nonce`, `l3a_aud` and `l3a_nonce` under `checks_skipped`. |
| 1 | same L3a presented twice (4.1) | verifier MUST reject a nonce already seen | valid, valid | valid, valid | The library keeps no nonce store. Replay detection belongs to the integrator. |
| 2 | L3a addressed to another audience (4.1) | verifier MUST check `aud` | **valid** | rejected | `aud` is checked only if the caller passes the expected value. Otherwise the check is skipped and `valid` stays True. |
| 3 | second L3a from the same L2 pair, fresh nonce (4.2) | the payment network MUST track issuance per L2 | valid, valid | n/a | By design, outside the library. The network's stateful log is the only control. |
| 4 | L3a amount 99,999 above the L2 cap of 40,000 (4.2 step 4) | reject | **valid** | **valid** | `verify_chain` does not evaluate constraints. A separate `check_constraints` call does reject it ("Amount exceeds maximum: 99999 > 40000 USD"). Public issue #38 asks about exactly this, with no reply. |
| 5 | L2 re-signed by a non-user key (4.3) | reject | rejected | rejected | "L2 signature verification failed (user key mismatch)". |
| 6 | checkout-payment mismatch, both L3s presented (4.4) | reject | rejected | rejected | Cross-reference check: `transaction_id != checkout_hash`. |
| 7 | the same mismatch, network sees only L3a (4.4) | spec §8.4: each party verifies its own L3; cross-reference when one verifier has both ("e.g., during dispute resolution") | valid | valid | `verify_chain` returned `valid=True`. Expected from a partial view. |
| 7b (4.4c in results.json) | the same mismatch, merchant sees only L3b (added after review, 10-22) | same as 7 | n/a | valid | `verify_chain` returned `valid=True`. **The merchant cannot detect it either.** L3b's own checkout is internally consistent, and the changed `transaction_id` is only in L3a. |
| 8 | L3a with `alg=none`, signature stripped (4.5) | reject | rejected | rejected | Rejected as a signature failure. |
| 9 | L3a expired 200 s ago, default skew (4.6) | RECOMMENDED 300 s tolerance | valid | valid | Accepted by design. |
| 10 | same, verifier skew 60 s (4.6) | reject | rejected | rejected | A tighter skew works when configured. |
| 11 | checkout and payment mandates bind different agent keys (4.9) | reject | rejected | rejected | "L2 mandate cnf.jwk values must be identical across all pairs but differ". |

**What it says.** The library's cryptographic checks held on every tampering case (5, 6, 8, 10, 11). Every case that was accepted is one where the spec makes a different party responsible:
- the integrator, for aud, nonce, replay and constraint evaluation (1, 2, 4);
- the payment network, for issuance count and budget (3);
- the party that holds both L3s, for the checkout-payment cross-reference (7, 7b). Spec §8.4 places that comparison wherever both are available, for example in dispute resolution.

The observed results follow the reference API's separation of checks. The spec states these delegations (security-model §4.1, §4.2, §8.4), and `checks_skipped` reports the skipped checks. Whether the API should also expose a combined verdict is what [upstream issue #38](https://github.com/agent-intent/verifiable-intent/issues/38) asks.

A signed mandate proves what the agent was allowed to do. Whether a deployment enforces the delegated checks is a property of that deployment, and this probe does not test any deployment.

## Correction (2026-10-22, after external review)

The first version of this report said the merchant-side check catches the case-7 mismatch. **It does not.** Case 7b shows a merchant holding only L3b cannot see a changed L3a `transaction_id`. Spec §8.4 says each party verifies its own L3 independently and the cross-reference runs when one verifier has both. So 'network accept plus merchant accept' is not a failure of either role. The open question is integration evidence: which component compares the references, and when that comparison affects authorization or fulfillment. The probe establishes the limits of a partial view. It does not establish how any deployed payment flow handles them. The related test proposal, [agent-security-harness #664](https://github.com/msaleme/red-team-blue-team-agent-fabric/issues/664), was corrected the same day.
