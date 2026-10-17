# Vocabulary crosswalk

Papers on the gap between what an agent was approved to do and what it executed use many
names for overlapping properties. This table lets a reader of any one of them find the ABV
vector, if any, that executes the failure that paper names, so the failure can be run against
a checker rather than only read about.

**This is not a priority claim.** Several of these papers predate ABV (Weng, arXiv
2606.02668, 1 Jun 2026, is the earliest listed here), and none of them cites it. The terms are
the authors' own, quoted verbatim; the failure descriptions paraphrase what each paper says in
the section named in the *Read* column, and are not claims about what any paper should have
said. Where a paper's term is broader than anything ABV tests, the row says so.

## How to read the vector column

- **Vector IDs** are quoted from `vectors/`. A listed vector executes the failure, or the
  named sub-case of it, in ABV's neutral record shape (`SPEC.md`).
- **partial** means ABV executes one named sub-case and not the rest.
- **none** means no ABV v0.1 vector executes the failure. An honest *none* is the useful
  answer: it marks where the corpus stops. ABV tests one record per execution (action,
  argument bytes, dereferenced bytes, expiry, separate attester, single use). It does **not**
  model revocation, session/task/context binding, executor or delegate identity, transitive
  or downstream effects, approval rendering, policy state, or populations of agents
  (`SPEC.md`, "What this corpus does not test").
- ABV checks bytes under RFC 8785 canonicalization. Where a paper's property is over
  *semantic* meaning (ReSA, CAVA, CXI), an ABV vector is a byte-level instance of that
  failure, not a test of the paper's semantics.

## Crosswalk

| # | Term (verbatim) | Paper | Read | Failure it names | ABV vector(s) |
|---|---|---|---|---|---|
| 1 | Consent Integrity | arXiv 2606.02668, Weng, 1 Jun 2026 | Abstract; Def. 1 | The human approves an agent-written summary, so a different action can run under that consent. Def. 1 has four conditions: truthful rendering, faithfulness, trusted path, bind-to-execution. | partial: `NEG-P1-01`, `NEG-P2-01`, `NEG-P2-02` (condition 4, bind-to-execution, only). Conditions 1–3 concern rendering and the consent channel: none. |
| 2 | Silent approval bypass | arXiv 2606.02668, Weng, 1 Jun 2026 | Def. 2 | A security-relevant action executes after approval without the mediator rendering the relevant fact or flagging it uninspectable. | none (rendering is not modeled) |
| 3 | reconstruction-stable authorization (ReSA) | arXiv 2609.26529, Zhu, Liu, Fan, Chen, He, 22 Sep 2026 | Abstract; §2.1, Eq. 1 | The action shown for approval is not the object consumed at the sink: reload, transcript projection, argument rebinding or durable-state lookup reconstruct it first. ReSA requires every executed meaning under a grant to lie within the grant's scope; it excludes nonce, expiry and multiplicity. | `NEG-P1-01`, `NEG-P2-01`, `NEG-P2-02`, `NEG-P3-01`, `NEG-P3-02` (byte-level instances; ReSA is over normalized semantic meaning) |
| 4 | approval laundering; closure-bound approval | arXiv 2609.28586, Zhang, Xia, Wu, Yue, Zhang, Cheng, Tu, 23 Sep 2026 | Abstract; §1 | A durable record faithfully names the entry invocation but leaves at least one effect of its transitive workflow (lifecycle hooks, MCP network authority) unbound. | none. The invocation record matches, which is what ABV checks; transitive effects are outside the record. |
| 5 | Scope Laundering | arXiv 2609.38983, Wang, 30 Sep 2026 | §II-E; Table II | An approved call dispatched exactly as approved reaches a resource beyond what the granted pattern suggests, e.g. via a child process. | none (effect divergence with unchanged fields) |
| 6 | Argument Laundering | arXiv 2609.38983, Wang, 30 Sep 2026 | Table II | An approved command dispatched unchanged has its effect broadened by a repository-local mechanism its arguments never name, e.g. a version-control hook. | none. Not ABV P2: the argument bytes match. Same word, different failure. |
| 7 | Temporal Laundering | arXiv 2609.38983, Wang, 30 Sep 2026 | Table II; §III-A | An approval granted in one session, or as a persistent rule, is exercised in a later session without fresh confirmation (a `session_id` binding failure, not expiry). | partial: `NEG-P6-01`, `NEG-P6-02` (one approval, second execution, under ABV's single-use profile). Session binding: none. |
| 8 | Tool Laundering | arXiv 2609.38983, Wang, 30 Sep 2026 | Table II | A call approved for tool T1 is dispatched through a never-approved T2; or the program a command name resolves to at execution differs from the one observed at approval. | partial: `NEG-P1-01` (first disjunct). Name resolution at execution: none. |
| 9 | Delegation Laundering | arXiv 2609.38983, Wang, 30 Sep 2026 | Table II | A main-session approval is inherited without re-approval by a subagent under a different `agent_id`. | none (executor identity is not bound to the approval) |
| 10 | Semantic Laundering | arXiv 2609.38983, Wang, 30 Sep 2026 | Table II | The text shown in the approval prompt does not faithfully disclose the command being authorized. | none (rendering is not modeled) |
| 11 | Loopjacking | arXiv 2609.21081, Kumar, 17 Sep 2026 | Abstract | A human approves operation A and the implementation uses that decision for a materially different B: either B was encoded but omitted or misrepresented at approval (representation-based), or mutable state replaced A with B after approval (post-approval state substitution). | partial: `NEG-P1-01`, `NEG-P2-01`, `NEG-P2-02`, `NEG-P3-01` (post-approval substitution). Representation-based variant: none. |
| 12 | Approval-binding invariant | arXiv 2609.21081, Kumar, 17 Sep 2026 | "Approval-binding invariant" paragraph | Authorizing an operation whose complete use-time form is not materially equivalent to what was reviewed, or whose decision is no longer valid for the current principal, task and scope. | partial: `NEG-P1-01`, `NEG-P2-01`, `NEG-P2-02`, `NEG-P3-01` (equivalence at use time). Validity for principal, task, scope: none. |
| 13 | security-context discontinuity; end-to-end consequence integrity (ECI) | arXiv 2609.05269, Zheng, Yang, 4 Sep 2026 | Abstract | Composed controls fail when a boundary drops a source label, accepts a self-declared authority root, widens a delegation, changes an approved field without a valid transformation relation, or executes a stale or replayed permit. | partial: changed field `NEG-P2-01`, `NEG-P2-02`; stale (expired) permit `NEG-P4-01`; replayed permit `NEG-P6-01`, `NEG-P6-02`; self-attested approval `NEG-P5-01`. ABV has no vector with an attester key unknown to the verifier. Source labels, delegation widening: none. |
| 14 | residual-authority replay | arXiv 2609.33910, Zhang, Wang, Li, Wang, Sun, Dai, 27 Sep 2026 | Abstract; §1 | Approvals persisted across tasks or sessions outlive the context that justified them; an attacker farms them through benign tasks and replays them later. | partial: `NEG-P6-01`, `NEG-P6-02` (a grant used for a second execution, under ABV's single-use profile). Context binding: none. |
| 15 | schema-epoch drift; formation-consistent dispatch (FCD) | arXiv 2609.35088, Kim, Kang, 28 Sep 2026 | Abstract | An unchanged, schema-valid call acquires a different security effect when the host selects a different implementation during rollout, reconnect or delayed approval. | none (the call record is identical; the handler is not part of the record) |
| 16 | authorization succession (conserves authority) | arXiv 2610.00347, Zhu, Wang, 29 Sep 2026 | Abstract; scope paragraph | Per-successor authorization does not constrain a population of self-modifying agents: siblings duplicate quotas, combine permissions, survive ancestor cuts, or overlap predecessors. | none (populations are not modeled) |
| 17 | Approval drift | arXiv 2607.13716, Wang, 15 Jul 2026 (CAVA) | Abstract; threat-model list | An operator approves one surface description while a different semantic action executes. | `NEG-P1-01`, `NEG-P2-01`, `NEG-P2-02` (byte-level). CAVA's other half, the same action across rewritten runtime forms, corresponds only at serialization level to positive controls `CTRL-02`, `CTRL-04`. |
| 18 | Context-to-Execution Integrity (CXI) | arXiv 2607.06000, Santos-Grueiro, 7 Jul 2026 | Abstract; §3.5 | A call executes without field authority, exact-effect authorization and invocation authority all binding to the same action manifest. | partial: exact value `NEG-P2-01`, `NEG-P2-02`; consumed invocation authority `NEG-P6-01`, `NEG-P6-02`. Field provenance, effect computation: none. |
| 19 | authorization continuity | arXiv 2607.23586, Zhang, Zhang, 26 Jul 2026 | Abstract | An agent evolves under a live grant (skills, tools, workflows, delegation), so the subject or context exercising the grant no longer matches what the user evaluated. | none |
| 20 | safety-compliant mission hijacking | arXiv 2609.31110, Chepuri, Srivastava, 25 Sep 2026 (AuthGuard-R) | Abstract | A robot action that is physically safe but violates the authenticated mission: redirected delivery, substituted object, extended region, unnecessary sensor, delay. | none (ABV approvals scope one action, not a mission policy) |
| 21 | Agent Secret Use (ASU); authorization by exposure | arXiv 2604.24920, Yu, Geng, Zeng, Knottenbelt, 27 Apr 2026 (SUDP) | Abstract | Enabling an action places a reusable secret inside a model-steerable boundary, so a transient compromise becomes durable account compromise. | none (secret exposure is not modeled; ASU's operation-bound and single-use requirements correspond to P1, P2, P6) |
| 22 | authorization-to-effect closure | arXiv 2608.21159, Tong, Dai, Guo, 21 Aug 2026 (AID-Guard) | Abstract | Authorization ends at admission: the request changes before commit, or a replacement after a lost response creates a second effect from one approval. | partial: `NEG-P2-01`, `NEG-P2-02` (request changed); `NEG-P6-01`, `NEG-P6-02` (second effect). Provider state, ambiguous outcomes: none. |
| 23 | stale authorization; policy-state serializability | arXiv 2608.02764, Peng, Wu, 3 Aug 2026 (Provenact) | Abstract | Budgets, inventory, approval status or risk signals change between request and effect, so an earlier authorization is stale when the effect commits. | none (`NEG-P4-01`, `NEG-P4-02` test expiry only; policy state is not modeled) |
| 24 | execution-bound authorization | arXiv 2610.14245, Heydari Shahna, Kim, Jung, Park, Mattila, Kim, 9 Oct 2026 | Full paper (§III–IV) | In the approval–dispatch–execution interval, a substituted motion, a stale or revoked approval, a replayed lease, or a loaded skill that outlives its permission. | partial: substituted action or motion `NEG-P1-01`, `NEG-P2-01`, `NEG-P2-02`; expired lease `NEG-P4-01`; replayed lease `NEG-P6-01`, `NEG-P6-02`. Revocation before dispatch or during execution: none. |
| 25 | Binding drift (M2) | arXiv 2610.11754, Waks, Glocker, 8 Oct 2026 | Full paper (§2–3) | A human authorizes plan *v*; a later compiler, config edit or backend executes something else, and a plan hash stored in a report does not bind the executable. | partial: `NEG-P2-01`, `NEG-P2-02`, `NEG-P3-01`, `NEG-P3-02`. The compiler chain is not modeled. |
| 26 | Human-authenticated gates (targets self-approval) | arXiv 2610.11754, Waks, Glocker, 8 Oct 2026 | Full paper (§3.1, P4) | An agent creates its own effective approval, waiver or promotion; "Chat confirmation is not approval." | `NEG-P5-01`, `NEG-P5-02`. P5 tests a separate, known attester, not that the attester is a human or is entitled to approve. |

26 rows: 14 name at least one ABV vector (3 full, 11 partial), 12 are none.

Two naming collisions matter in practice. "Approval laundering" names different failures in
Zhang et al. (row 4) and Wang (rows 5–10), which do not cite each other. Wang's "Argument
Laundering" (row 6) is not ABV P2: the argument bytes match and the effect still widens.

## Not yet read at claim level

Listed so they are not mistaken for omissions. No failure description is given, and no
vector mapping is claimed, until the relevant section has been read.

| Term | Paper |
|---|---|
| Evidence-bound autonomous research (EviBound) | arXiv 2511.05524, Chen, 28 Oct 2025 |
| ClaimReceipt (evidence sufficiency and coverage) | arXiv 2609.01992, Zhu, Chang, 2 Sep 2026 |
| DGF-Bench (deception against multi-agent governance boards) | arXiv 2609.34913, Canale, 28 Sep 2026 |
| Action-Bound Approval Protocol | Microsoft Agent Governance Toolkit, ADR 0030 (not on arXiv) |

## Corrections

If a row misstates a paper, open an issue quoting the passage. The paper's own wording wins.
