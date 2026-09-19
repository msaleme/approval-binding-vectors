# Observed referents

Every predicate in ABV has at least one referent in a real specification, read at a pinned
version on 2026-09-19. None was invented for symmetry. Where a gap is a **declared scope
decision** rather than an oversight, that is recorded as such.

| Predicate | Observed in | What was observed |
|---|---|---|
| **P1 / P2** | CognOS LUMEN v0.1 (`acprofessionale/CognOS-Constitutional-Engineering-Framework` @ `c7c4f7d`) | `governance.approval.scope_digest` commits `{arguments_sha256, tool}` jointly. The published negative vector is integrity-valid and scope-mismatched; both recomputed independently. LUMEN satisfies P1 and P2 — it is the corpus's positive referent for them. |
| **P1 / P2** | Agent Security Harness RCL suite | Decomposes authorization into two predicates rather than one joint digest, so a wrong tool and wrong arguments fail separately. Referent for why P1 and P2 are split here. |
| **P3** | `draft-laxsharma-pact-02` §5.1 | *"Every URI carried inside hash-committed content MUST be accompanied by a sibling hash over the dereferenced bytes."* Added after the `-00` revision committed `harness_uri` as a string, which *"permitted a Buyer to substitute the acceptance instrument after signature, run the substituted instrument, and submit the failure as a valid proof of nonconformance."* `NEG-P3-02` is that failure in neutral form. |
| **P3** | Microsoft AHP, `types/channels-chat/state.ts` | `ToolInput = string \| ContentRef`; `ContentRef` is `{uri, sizeHint?, contentType?, nonce?}`. Doc comment: *"Referenced input is mutable until the tool call leaves `pending-confirmation`."* The approval names a reference to mutable content. |
| **P4** | CognOS LUMEN v0.1 | The passport carries `governance.approval.expires_at` (`2026-09-16T12:00:00Z`) against `recorded_at` of `10:00:00Z`. The field exists and **the published reference verifier does not check it** — established by reading `reference/lumen_verify.py` at the pinned commit, where `expires_at` does not appear and the checks performed are: required members, `schema_version`, imprint factor/weight/tier arithmetic, deny-cannot-have-executed, ask-requires-approved, `scope_digest` match, and content digest. Evidence basis is source reading, not digest recomputation — recomputation could not have shown this. |
| **P4** | Agent Security Harness RCL suite | Applies a freshness window to the checker transcript only, not to the authorization claim. Same gap from the other side — which is why P4 is in this corpus rather than assumed. |
| **P5** | CognOS LUMEN v0.1 | The passport is a single document with one content digest and **no per-authority signatures**, so the approval status and the truth claim are both assertions by whoever wrote it. |
| **P5** | Microsoft AHP | `ToolCallConfirmationReason` is `not-needed \| user-action \| setting` — no principal, no timestamp, no input commitment. Across `docs/specification/` and `types/`: `digest`, `hash`, `sha256`, `signature` occur **0 times each**. |
| **P6** | Microsoft AHP issue #266 | Single-use is not in the current model; the thread's open envelope questions include replay protection. Recorded as an open design question, not a defect. |
| **Canonicalisation** | CognOS LUMEN v0.1 | Substitutes a zero value into `integrity.content_sha256` before hashing. An implementation that removes the field instead computes a different digest for an identical document — verified by independent recomputation. |
| **Canonicalisation** | `draft-laxsharma-pact-02` Table 3, V-25 | *"a number serialized by the host language's default formatter, such as 1.0 for the float one"* → digest mismatch. |

## Declared scope, not defect

**AHP's trust model is stated, not accidental.** Issue #266 opens: *"AHP's current trust
model intentionally does not assume the host is compromised — a deliberate, reasonable
starting point."* AHP appears in this corpus because it is the clearest published example of
an approval bound to a mutable reference, **not** because it fails to meet a commitment it
made. Any use of this corpus that reports AHP as non-conforming without that sentence is
misusing it.

The same applies to PACT, which is an individual Internet-Draft with a prototype
implementation and no working group, and to LUMEN, which is a seven-week-old solo project
whose author published his own negative vector and explicitly declined to treat his passing
test as independent validation. Report each at its own weight.
