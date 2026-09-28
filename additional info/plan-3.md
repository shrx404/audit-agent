# PLAN.md - AuditMemory: A Compliance and Audit Agent With Memory

> Hackathon: AI Agents That Learn Using Hindsight
> Problem statement: Compliance and Audit Agent
> Pitch line: **"Auditors remember everything you got wrong last year. Your team doesn't. We fix that."**
> **MVP goal: An AI compliance agent that remembers past audit findings, root causes, remediations, policy changes, and control history, then detects when a new issue may be repeating an old failure.**
> **Build window: 11 to 12 hours. MVP only.**

---

## 0. How To Use This File

- This file is the single source of truth. Put it in the repo root next to `AGENTS.md`.
- Every task has an ID like `T2.3`. Tick the box when done. Commit after each ticked box.
- Sections marked **[VERIFY]** contain things agents commonly get wrong. Check them by hand.
- Everything in this file is **MVP** unless it is marked **[POST-MVP]** or **[STRETCH]**. Those items live in Section 16 and are **not built** in the 11 to 12 hour window.
- The MVP priority order is fixed. Do not start a step until the previous one passes its exit check:
  1. Hindsight hello-world
  2. Seed 20 to 30 memories
  3. New finding input
  4. Recall relevant history
  5. Recurrence analysis
  6. Show past root cause and remediation
  7. Analyst confirmation
  8. Retain confirmed outcome
  9. Prove changed behavior on the next query
- A pretty UI on a broken memory loop scores badly. The UI is built against a mock in parallel, but it is only "done" when the real loop in step 9 passes.

---

## 1. Hackathon Rules Recap (from the official doc)

### 1.1 Hard requirements

- [ ] All teams MUST build using **Hindsight**
- [ ] Project must clearly demonstrate how Hindsight memory is used
- [ ] Submit: **GitHub repo** (clean, documented code)
- [ ] Submit: **Demo video** showing the agent in action
- [ ] Submit: **Live demo** to judges
- [ ] Submit: **Explanation of how Hindsight memory is used** (goes in README)
- [ ] EVERY team member completes: **Article + Social Media post + Video** from the official content guide (done in parallel to the build, see Phase 8)
- [ ] Share the project based on the official content guide challenges

### 1.2 Judging weights and what we do about each

| Criteria                 | Weight | What judges look for                   | Our MVP answer                                                                                                                                                              |
| ------------------------ | ------ | -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Innovation               | 30%    | Fresh take, beyond chatbot territory   | Recurrence detection that separates "same control" from "same failure". Compares failure type, root cause, org context, and past remediation, not just control IDs         |
| Use of Hindsight Memory  | 25%    | Memory central, agent visibly improves | No memory, no verdict (empty-bank check). Every result shows the memories used. Analyst-confirmed outcomes are retained and change the very next analysis                    |
| Technical Implementation | 20%    | Clean, architected, handles edge cases | Typed schemas, trust levels, temporal resolver, guardrails on LLM output, LLM retry and fallback, scenario tests                                                            |
| User Experience          | 15%    | Intuitive, compelling demo flow        | One flow: New Finding, Analyze, Recurrence Result, Past Memory Evidence, Confirm or Correct                                                                                  |
| Real-world Impact        | 10%    | Genuine problem, path to adoption      | Repeat audit findings are the costliest kind. Analysts today re-discover the same root cause every year                                                                     |

### 1.3 Doc guidance we must follow

- **Avoid student-centric projects.** Compliance is a professional workflow. Good.
- **Keep scope tight:** one workflow, one persona, one value proposition.
- **Realistic data is the number one thing** that makes it look real. Budget real time for it (about 1 hour, hand-written).
- **Show the learning:** the same kind of finding is analyzed before and after the analyst confirms an outcome, and the answer visibly changes.
- **Handle function calling errors** with the recommended Groq models.
- **Think like a demo:** value obvious in 60 seconds.

---

## 2. Product Definition

### 2.1 One-liner (MVP goal)

An AI compliance agent that remembers past audit findings, root causes, remediations, policy changes, and control history, then detects when a new issue may be repeating an old failure.

### 2.2 Persona and scenario (fixed, do not change)

- **Company:** FinPay (fictional fintech, 120 employees, payments API)
- **Persona:** Arjun Mehta, Compliance Manager
- **Situation:** SOC 2 Type II audit is 30 days away. New findings and observations keep arriving from internal checks and pre-audit reviews. Arjun must decide fast: is this new, or is it the same failure we already "fixed"?
- **Frameworks in scope:** SOC 2 Trust Services Criteria (Security focus)
- **History available:** about 26 seeded memories covering 2023 to 2026 (findings, root causes, remediations, policy changes, control history, org events)

### 2.3 The main MVP workflow

```
New Finding
   -> Hindsight Recall
   -> retrieve similar past findings, root causes, remediations
   -> compare with the current issue
   -> possible recurrence (marked "suspected")
   -> analyst confirms or corrects
   -> retain the confirmed new outcome into Hindsight
   -> the next analysis uses it (behavior visibly changes)
```

Step by step:

1. **New Finding:** analyst submits `control_id`, `department`, `finding`, optional `evidence_ref`.
2. **Hindsight Recall:** the backend runs several recall queries built from the finding text, department, and root-cause and remediation wording. `control_id` is a search hint only.
3. **Retrieve:** past findings, root causes, remediations, policy changes, control tests, and org events come back, with dates and trust levels.
4. **Compare:** the agent compares the new issue against each past finding on five dimensions: semantic similarity, failure type, root cause, organizational context, and previous remediation (Section 3.5).
5. **Possible recurrence:** the result is always labeled **suspected**. It is never stored as a fact.
6. **Analyst confirms or corrects:** Arjun accepts, edits the root cause and remediation, or marks "not a recurrence".
7. **Retain:** only the analyst-confirmed result is retained into Hindsight as a trusted, dated memory.
8. **Changed behavior:** the next similar finding is analyzed against the new memory and the answer changes.

### 2.4 The four MVP capabilities

1. **Recall:** pull relevant past findings, root causes, remediations, policy changes, and control history for a new finding.
2. **Detect recurrence:** decide whether the new issue repeats an old failure, using memory-based comparison and not control ID matching. Deterministic rules only run the obvious checks (overdue test, stale ticket, missing evidence).
3. **Explain with evidence:** show previous root cause, previous remediation, and the exact memories used.
4. **Learn:** analyst-confirmed outcomes are retained and change the next analysis.

### 2.5 Explicit non-goals (say no to these)

- No real integrations with AWS, Okta, Jira, or any live system
- No support for frameworks beyond SOC 2 (mention ISO 27001 as roadmap only)
- No user accounts or authentication
- No document upload or PDF parsing
- No model training or fine-tuning of any kind
- No automatic retention of AI output. AI guesses never become trusted memory
- No readiness score, audit predictions, timeline chart, or learning-curve chart in the MVP (see Section 16)

---

## 3. Architecture

### 3.1 Diagram

```
        +-----------------------------------------------+
        |              Next.js Frontend (1 page)         |
        | New Finding -> Result -> Evidence -> Confirm   |
        +---------------------+-------------------------+
                              | REST (JSON)
        +---------------------v-------------------------+
        |                FastAPI Backend                |
        |  POST /analyze-finding    POST /confirm-finding|
        |                                               |
        |  recall_builder -> temporal resolver          |
        |        -> judge (LLM) -> guardrails           |
        |  checks.py (deterministic: overdue/stale/     |
        |             missing evidence)                 |
        |  analysis registry (in-process, "suspected")  |
        +------+----------------------------+-----------+
               |                            |
     +---------v----------+        +--------v---------+
     |     Hindsight      |        |     Groq LLM     |
     |  retain (seed +    |        |  gpt-oss-120b    |
     |   confirmed only)  |        |  qwen3-32b       |
     |  recall (history)  |        |  (fallback)      |
     |  reflect (advisory,|        +------------------+
     |   timeboxed)       |
     +--------------------+
```

Division of labor (this is the core design rule):

| Layer                    | Responsible for                                                                                          |
| ------------------------ | -------------------------------------------------------------------------------------------------------- |
| **Hindsight**            | All historical memory: what happened, why, how it was fixed, what changed since, what the analyst confirmed |
| **LLM judge (Groq)**     | Comparing the new finding to the recalled memories and rating the five dimensions. Uses only recalled text |
| **Guardrails (code)**    | Enforcing "same control alone is never recurrence", citations required, no-history handling               |
| **Deterministic rules**  | Only obvious checks: overdue tests, stale tickets, missing evidence. Never decides recurrence              |

### 3.2 Tech stack

| Layer     | Choice                                                 | Why                                 |
| --------- | ------------------------------------------------------ | ----------------------------------- |
| Frontend  | Next.js, TypeScript, Tailwind (single page)            | Your existing stack                 |
| Backend   | FastAPI, Pydantic v2                                   | Typed schemas, your existing stack  |
| Memory    | Hindsight Cloud (`hindsight-client` Python SDK)        | Required by rules                   |
| LLM       | Groq: `openai/gpt-oss-120b`, fallback `qwen/qwen3-32b` | Recommended by doc, fast, free tier |
| Data      | JSON seed files plus in-process analysis registry      | No database needed                  |

Charts (Recharts) and streaming (SSE) are **[POST-MVP]**.

### 3.3 Hindsight API surface we use **[VERIFY]**

From the official docs (confirm against the live docs before coding):

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="https://<your-cloud-url>", api_key="<key>", timeout=30.0)

# Retain (store)
client.retain(bank_id="finpay-audit", content="...", context="audit finding", timestamp="2024-06-15T10:00:00Z")

# Recall (search)
results = client.recall(bank_id="finpay-audit", query="access review not performed")
for r in results.results:
    print(r.text)

# Reflect (synthesize), used only as a timeboxed advisory step in the MVP
answer = client.reflect(bank_id="finpay-audit", query="Does this repeat a past failure?")
print(answer.text)
```

Notes:

- Recall runs several strategies in parallel (semantic, keyword, graph, temporal), so include **dates**, **control IDs**, and **finding and ticket IDs** in retained text. That makes keyword and temporal recall work well.
- Check whether the Cloud SDK constructor needs `api_key`. The quickstart shows a local URL. **Do not let an agent guess this.**
- **[VERIFY] in the hello-world (T0.4 to T0.6), write results into `docs/hindsight-notes.md`:**
  - Does `retain` accept `document_id`, `metadata`, or `tags`? (Needed for idempotent seeding and for mapping results back to memory IDs.)
  - Is `retain` synchronous, or is extraction async? How long until a retained memory shows up in `recall`? (Needed for the "changed behavior on the next query" proof.)
  - Do the `[MEM ...]` header tokens and IDs (`M-004`, `F-2024-03`) survive in recalled text? If Hindsight rewrites them, map results back through `document_id` or metadata instead.
  - What fields does a recall result carry (text, score, date, id)?
  - How do we create a fresh bank or delete one? (Needed for `scripts/reset_demo.py`.)
- The client may need `nest_asyncio` inside notebooks. Not needed in FastAPI, but relevant for scratch testing.

### 3.4 Memory design (this is 25% of the score, think hard here)

**One bank:** `finpay-audit` (set by `HINDSIGHT_BANK_ID`; the reset script uses a fresh bank ID per demo run).

**What we retain, as separate memories.** Each is a short, self-contained natural-language paragraph, because Hindsight extracts entities and facts from text. Every memory starts with a one-line header so we can parse it in code:

```
[MEM M-004 | type=finding | trust=verified | subject=F-2024-03 | as_of=2024-03-12 | supersedes=none]
On 2024-03-12, the SOC 2 auditor raised finding F-2024-03 against control CC6.2 (access reviews) in the Engineering department: quarterly production admin access reviews were not performed for Q4 2023 and Q1 2024. Severity: High.
```

| Memory type            | Example content                                                                                                                                                | Context tag             |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| Audit finding          | "On 2024-03-12 ... finding F-2024-03 against CC6.2 (Engineering): quarterly access reviews were not performed. Severity: High."                                | `audit finding`         |
| Root cause             | "Root cause of F-2024-03, recorded 2024-03-25: the Feb 2024 reorg moved the review owner (Priya Nair) to another team and no backup owner was named."           | `root cause`            |
| Remediation            | "Ticket REM-118 opened 2024-03-20, owner Rahul Iyer, to fix F-2024-03. Marked done on 2024-06-01. Evidence attached: none."                                    | `remediation`           |
| Policy change          | "On 2024-09-01 access management policy v3 (POL-ACCESS) moved production admin reviews from quarterly to monthly. Supersedes v2."                               | `policy change`         |
| Control history        | "Control CC6.2 was last tested 2025-04-15 by Anita Rao. Result: partial. Policy requires testing every 90 days."                                                | `control test`          |
| Org event              | "In 2024-02 the platform team was reorganized and three admins left or changed teams."                                                                         | `org event`             |
| Analyst confirmation   | "ANALYST-CONFIRMED on 2026-09-28 by Arjun Mehta: finding NF-2026-01 (CC6.2, Support) repeats F-2024-03. Confirmed root cause: ... Confirmed remediation: ..."   | `analyst confirmation`  |

**Rules for writing memories:**

- Always include: date, control ID, finding or ticket ID, department, owner, status
- One fact cluster per retain call (do not dump a whole spreadsheet in one call)
- Use consistent ID formats so keyword recall works: `F-YYYY-NN`, `REM-NNN`, `CC6.2`, `M-NNN`, `M-CONF-NNNN`
- Set `timestamp` on every retain so temporal recall works
- Keep root cause and remediation in their own memories, linked to the finding by ID, so recall can return them independently

**Memory safety and trust levels (MVP rule):**

| Level       | Meaning                                                                 | Stored in Hindsight? | How it is used                                              |
| ----------- | ----------------------------------------------------------------------- | -------------------- | ----------------------------------------------------------- |
| `verified`  | Seeded historical record, or a fact the analyst explicitly confirmed    | Yes                  | Trusted evidence. Cited in explanations                     |
| `suspected` | Anything the AI inferred: possible recurrence, guessed root cause, etc. | **No**               | Shown in the UI with a "Suspected" badge. Held only in the in-process analysis registry until the analyst acts |

Rules:

- `/analyze-finding` **never calls `retain`**. Its output is always `status: "suspected"`.
- Only `/confirm-finding` can call `retain`, and only with analyst-provided or analyst-accepted content. Accepting the AI's suggested text is an explicit action in the UI, and it is recorded as the analyst's confirmation.
- If the analyst rejects a suspected link ("not a recurrence"), that rejection is retained as a verified memory too. Rejections are facts that stop the same false match from repeating.
- A test asserts that no retain call happens during analysis (T4.2).

**Temporal handling (MVP rule):**

- Every memory has `as_of` (the date the state became true) and `subject` (the thing whose state it describes, for example `POL-ACCESS`, `REM-118`, `CC6.2:owner`).
- When several verified memories share a subject, the one with the **newest `as_of`** is the **current state**. Older ones are kept and shown as **history**, never deleted or hidden.
- A memory may declare `supersedes=<mem_id>`. The resolver uses `supersedes` first, then `as_of`.
- Example: `POL-ACCESS` v2 (quarterly, 2023-01-10) is history. `POL-ACCESS` v3 (monthly, 2024-09-01) is current. The agent says "the policy now requires monthly reviews" and can mention that it used to be quarterly.
- Analyst-confirmed memories are newer than seeded ones, so on conflict the confirmed state wins.
- The resolver is plain code that runs on parsed headers, not an LLM call, and is unit tested (T2.3).

**How each Hindsight operation is used (this goes in the README explanation):**

- **Retain:** loads the seeded history at startup, and later retains every analyst-confirmed outcome (confirmed recurrence, corrected root cause, confirmed remediation, or confirmed "not a recurrence")
- **Recall:** pulls relevant history for each new finding using several queries (finding text, department context, root cause and remediation wording). This is the engine of recurrence detection
- **Reflect:** one timeboxed advisory call per analysis, giving memory-based reasoning over the recalled history. If it fails or takes longer than 10 seconds, the analysis continues on recall alone

### 3.5 Recurrence logic (fixes the "same control ID" trap)

**Same `control_id` alone must NOT mean recurrence.** A control such as CC6.2 can fail in many different ways. Control ID is only a recall hint.

**Step 1: Recall.** Run 3 queries and merge and dedupe (cap about 15 memories):

1. The finding text as written
2. Department plus the failure described (for example "Support access review not performed")
3. Root cause and remediation phrasing ("why did this happen, how was it fixed, what changed in policy or ownership")

**Step 2: Resolve time.** Group by `subject`, mark `is_current` and `superseded_by` (Section 3.4).

**Step 3: Judge.** The LLM receives the new finding plus the recalled memories (with IDs, dates, trust, and current or history flags). For each candidate past finding (max 5) it rates five dimensions as `match`, `partial`, `none`, or `unknown`, each with a one-line reason and cited memory IDs:

| Dimension                | Question                                                                                   |
| ------------------------ | ------------------------------------------------------------------------------------------ |
| Semantic similarity      | Do the two issues describe essentially the same event or gap in plain language?            |
| Failure type             | Is it the same kind of failure (for example "review not performed" vs "approval bypassed")? |
| Root cause               | Does the recorded cause of the old finding plausibly explain the new one?                  |
| Organizational context   | Same team, ownership gap, reorg, tooling, or departure pattern?                            |
| Previous remediation     | Was the old fix incomplete, unevidenced, reopened, or out of scope for this case?          |

Judge rules: use only the provided memories, never invent history, output `unknown` when memory is silent, cite memory IDs for every claim, treat analyst-confirmed memories and rejections as stronger than seeded ones, treat the current state as authoritative and history as context.

**Step 4: Guardrails (code, after the LLM):**

```
possible_recurrence = True only if:
    failure_type == match
    AND (root_cause in {match, partial} OR remediation in {ineffective, unverified})
    AND semantic_similarity in {match, partial}
```

- Same `control_id` with `failure_type == none` is returned in `related_past_findings` with `is_recurrence_candidate = false`. It is shown as "related, not a recurrence"
- Different `control_id` with matching failure type and root cause **can** be a recurrence
- Confidence: `high` if failure type, root cause, and remediation evidence all point the same way. `medium` if two do. `low` otherwise
- No recalled findings: `possible_recurrence = false`, warning `no_history`, never invent
- Any claim without a cited memory ID is dropped
- Malformed judge JSON: strip fences, retry once, then fall back to the second model, then return a clear error object

**Step 5: Deterministic checks (obvious rules only), attached as `deterministic_checks`:**

| Check            | Rule                                                                                             |
| ---------------- | ------------------------------------------------------------------------------------------------ |
| `overdue_test`   | `today - last_tested > required_frequency_days` for the control (from `control_tests.json`)     |
| `stale_ticket`   | An open remediation for the control older than 180 days, or whose owner is not in `staff.json`   |
| `missing_evidence` | The new finding has no `evidence_ref`, or a related remediation is `done` with `evidence_ref = null` |

These rules never decide recurrence. They read structured seed records only. Known MVP limitation: analyst confirmations affect memory-based reasoning, not the structured JSON used by these three checks.

### 3.6 Data schemas (Pydantic and TypeScript must match)

```python
Trust = Literal["verified", "suspected"]
Rating = Literal["match", "partial", "none", "unknown"]

# ---- Structured seed records (also the source for memory text) ----
class Finding(BaseModel):
    id: str                 # F-2024-03
    control_id: str         # CC6.2
    control_name: str
    department: str
    severity: Literal["low", "medium", "high"]
    raised_date: date
    auditor_note: str
    audit_cycle: int        # 2024
    failure_type: str       # seed/eval ground truth only, NOT shown to the judge

class Remediation(BaseModel):
    id: str                 # REM-118
    finding_id: str
    owner: str
    opened_date: date
    marked_done_date: date | None
    evidence_ref: str | None
    status: Literal["open", "done", "verified"]

class ControlTest(BaseModel):
    control_id: str
    last_tested: date
    tester: str
    result: Literal["passed", "failed", "partial"]
    required_frequency_days: int

# ---- Memory ----
class MemoryRecord(BaseModel):     # what the formatter produces and we retain
    mem_id: str                    # M-004 or M-CONF-0001
    type: Literal["finding", "root_cause", "remediation", "policy_change",
                  "control_test", "org_event", "analyst_confirmation"]
    trust: Literal["verified"]     # only verified memories are ever retained
    subject: str                   # F-2024-03, REM-118, POL-ACCESS, ...
    as_of: date
    supersedes: str | None
    text: str

class RecalledMemory(BaseModel):   # what comes back from recall
    mem_id: str
    type: str
    trust: Trust
    as_of: date
    subject: str
    is_current: bool
    superseded_by: str | None
    text: str
    relevance: float | None

# ---- Analyze ----
class NewFindingRequest(BaseModel):
    control_id: str
    department: str
    finding: str
    evidence_ref: str | None = None

class DimensionMatch(BaseModel):
    rating: Rating
    reason: str

class RecurrenceComparison(BaseModel):
    semantic_similarity: DimensionMatch
    failure_type: DimensionMatch
    root_cause: DimensionMatch
    org_context: DimensionMatch
    remediation: DimensionMatch

class RelatedFinding(BaseModel):
    finding_id: str
    control_id: str
    department: str
    raised_date: date
    summary: str
    same_control_id: bool          # informational only, never sufficient
    is_recurrence_candidate: bool
    comparison: RecurrenceComparison
    memory_ids: list[str]

class PreviousRootCause(BaseModel):
    text: str
    as_of: date
    source_mem_ids: list[str]

class PreviousRemediation(BaseModel):
    text: str
    outcome: Literal["effective", "ineffective", "unverified", "unknown"]
    evidence_ref: str | None
    source_mem_ids: list[str]

class Flag(BaseModel):             # deterministic checks only
    kind: Literal["overdue_test", "stale_ticket", "missing_evidence"]
    control_id: str
    severity: Literal["low", "medium", "high"]
    explanation: str
    sources: list[str]

class AnalyzeFindingResponse(BaseModel):
    analysis_id: str
    status: Literal["suspected"]                    # always, until confirmed
    possible_recurrence: bool
    recurrence_confidence: Literal["low", "medium", "high"] | None
    related_past_findings: list[RelatedFinding]
    previous_root_cause: PreviousRootCause | None
    previous_remediation: PreviousRemediation | None
    explanation: str
    memories_used: list[RecalledMemory]
    deterministic_checks: list[Flag]
    warnings: list[str]                             # e.g. "no_history", "reflect_skipped", "hindsight_degraded"

# ---- Confirm ----
class ConfirmFindingRequest(BaseModel):
    analysis_id: str
    decision: Literal["confirm_recurrence", "not_recurrence", "correct"]
    linked_finding_ids: list[str] = []
    confirmed_root_cause: str | None = None         # required unless decision == "not_recurrence"
    confirmed_remediation: str | None = None
    outcome: Literal["open", "remediated_with_evidence",
                     "remediated_no_evidence", "accepted_risk"] = "open"
    analyst: str                                    # "Arjun Mehta"
    note: str | None = None

class ConfirmFindingResponse(BaseModel):
    ok: bool
    trust: Literal["verified"]
    retained_mem_ids: list[str]                     # e.g. ["M-CONF-0001"]
    retrievable: bool                               # true once recall returns it
    message: str
```

---

## 4. Repository Structure

```
auditmemory/
├── PLAN.md
├── AGENTS.md
├── SPEC.md
├── README.md
├── .gitignore
├── .env.example
├── docs/
│   ├── hindsight-notes.md        # pasted real API notes + verified behavior
│   ├── demo-script.md
│   └── architecture.png
├── data/
│   ├── controls.json             # 8 to 10 SOC 2 controls (IDs and names)
│   ├── staff.json                # ~10 people with active flag (for stale-ticket rule)
│   ├── findings.json
│   ├── remediations.json
│   ├── control_tests.json
│   ├── memories.json             # the 20 to 30 seed memories (headers + text)
│   └── scenarios.json            # R1, R2, R1b, D1 inputs + expected outcomes
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── schemas.py
│   │   ├── memory/
│   │   │   ├── client.py         # Hindsight wrapper + retry
│   │   │   ├── seed.py           # memories.json -> retain
│   │   │   ├── formatter.py      # record or confirmation -> memory text with header
│   │   │   ├── recall.py         # multi-query recall, dedupe, header parsing
│   │   │   └── temporal.py       # current vs history resolver
│   │   ├── agent/
│   │   │   ├── llm.py            # Groq client + retry + fallback + JSON repair
│   │   │   ├── analyzer.py       # recall -> resolve -> judge -> guardrails
│   │   │   ├── checks.py         # deterministic overdue / stale / missing evidence
│   │   │   ├── registry.py       # in-process "suspected" analyses
│   │   │   └── prompts.py
│   │   └── routes/
│   │       ├── analyze.py        # POST /analyze-finding
│   │       └── confirm.py        # POST /confirm-finding
│   └── tests/
├── scripts/
│   ├── hello_hindsight.py
│   ├── validate_data.py
│   ├── seed_memory.py
│   ├── smoke_test.py
│   ├── learning_check.py         # proves changed behavior
│   └── reset_demo.py             # fresh bank + reseed
└── frontend/
    ├── package.json
    └── src/
        ├── app/page.tsx          # the single page
        ├── components/
        │   ├── NewFindingForm.tsx
        │   ├── RecurrenceResult.tsx
        │   ├── MemoryEvidencePanel.tsx
        │   └── ConfirmCorrectPanel.tsx
        └── lib/api.ts
```

Removed from the MVP tree and moved to Section 16: `readiness.py`, `predict.py`, `detect.py` (replaced by the smaller `checks.py`), `generate_data.py`, `eval_learning_curve.py`, `ReadinessGauge`, `FlagList`, `ControlTimeline`, `MemoryToggle`, `AskBox`, `FeedbackButtons`, and the `ask`, `readiness`, `feedback`, `memory`, `demo` routes.

---

## 5. The Data Plan (highest leverage, do it well, but keep it small)

### 5.1 Sources

- **Control backbone:** 8 to 10 real SOC 2 control IDs and names (CC6.1, CC6.2, CC6.3, CC7.2, CC8.1, CC9.2 and similar). Hand-pick from the Vanta Control Set (`VantaInc/vanta-control-set`) or from memory. Do not spend time parsing the full set.
- **Licensing:** the official SOC 2 criteria text is AICPA copyright. Use control names and IDs from open sets and **write your own descriptions**.
- **No Kaggle or OSCAL work in the MVP.**

### 5.2 What to author (by hand, LLM-assisted drafting is fine)

| File                 | Count           | Notes                                                         |
| -------------------- | --------------- | ------------------------------------------------------------- |
| `memories.json`      | **26**          | The seed memories in Section 5.3. Each with header and text   |
| `findings.json`      | 5               | Matches the finding memories                                  |
| `remediations.json`  | 7               | Matches the remediation memories                              |
| `control_tests.json` | 3               | CC6.2, CC7.2, CC8.1                                           |
| `staff.json`         | about 10        | Rahul Iyer and Divya Menon marked as left                     |
| `scenarios.json`     | 4               | Inputs and expected outcomes in Section 5.4                   |

### 5.3 The seed memory set (26 memories, target: written in about 1 hour)

| ID    | Type          | Gist                                                                                                                                              |
| ----- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| M-001 | finding       | F-2023-02, CC6.2, Engineering, 2023-03-14: quarterly production admin access reviews not performed. High                                          |
| M-002 | root cause    | F-2023-02: Security Lead left, no named owner, reviews depended on one person's calendar                                                          |
| M-003 | remediation   | REM-071, owner Priya Nair, done 2023-07-01, evidence EV-311. Verified                                                                             |
| M-004 | finding       | F-2024-03, CC6.2, Engineering, 2024-03-12: access reviews not performed Q4 2023 and Q1 2024. High                                                 |
| M-005 | root cause    | F-2024-03: Feb 2024 reorg moved Priya to platform, review duty not handed over, no backup owner                                                   |
| M-006 | remediation   | REM-118, owner Rahul Iyer, marked done 2024-06-01, **evidence: none**                                                                             |
| M-007 | remediation   | REM-118 state change 2024-11-18: internal check found no Q2 or Q3 2024 review evidence, reopened. Owner Rahul Iyer left 2025-01. **Supersedes M-006** |
| M-008 | finding       | F-2025-04, CC6.3, Support, 2025-05-06: contractor account active 21 days after contract end. Medium                                              |
| M-009 | root cause    | F-2025-04: HR offboarding tickets not linked to IAM deprovisioning                                                                                |
| M-010 | remediation   | REM-131: automated IAM deprovision on HR termination, done 2025-06-10, evidence EV-402. **Verified, resolved (decoy)**                            |
| M-011 | finding       | F-2024-09, CC8.1, Engineering, 2024-08-20: hotfix deployed to production without approval. Medium                                                |
| M-012 | root cause    | F-2024-09: emergency change path undocumented, no approver available after hours                                                                  |
| M-013 | remediation   | REM-140: emergency change procedure, done 2024-10-02, evidence EV-350. Verified                                                                   |
| M-014 | finding       | F-2023-06, CC9.2, Finance and Procurement, 2023-06-05: annual vendor security reviews not done for 4 critical vendors. High                       |
| M-015 | root cause    | F-2023-06: procurement lead left, ownership gap, no backup owner                                                                                  |
| M-016 | remediation   | REM-088: owner assigned, 2 of 4 vendors reviewed, done 2023-09-15, evidence EV-320 (partial)                                                      |
| M-017 | policy change | POL-ACCESS v2, 2023-01-10: access reviews quarterly                                                                                               |
| M-018 | policy change | POL-ACCESS v3, 2024-09-01: production admin reviews monthly. **Supersedes M-017**                                                                 |
| M-019 | policy change | POL-CHANGE v2, 2024-10-01: emergency change path and after-hours approver defined                                                                 |
| M-020 | control test  | CC6.2 last tested 2025-04-15 by Anita Rao, result partial (evidence for 2 of 4 quarters). Required every 90 days. **Overdue**                     |
| M-021 | control test  | CC7.2 backup restore test last run 2025-06-20, passed. Required every 12 months. **Overdue**                                                      |
| M-022 | control test  | CC8.1 tested 2025-11-05, passed. Required every 180 days                                                                                          |
| M-023 | org event     | 2024-02: platform reorg, three admins left or changed teams; review duties not reassigned                                                         |
| M-024 | org event     | 2025-01: Rahul Iyer (owner of REM-118) left FinPay                                                                                                |
| M-025 | org event     | 2025-03-10: Security Operations formed; RACI v1 assigns access-review ownership for production infrastructure admins only. **SaaS and internal tooling admin groups are not in scope** |
| M-026 | remediation   | REM-152, CC9.2, opened 2025-11-20, owner Divya Menon (left 2026-03), still open. **Stale, unowned**                                               |

Temporal pairs deliberately seeded: M-017 to M-018 (policy), M-006 to M-007 (ticket state), M-023 to M-025 (ownership context).

### 5.4 The MVP scenarios (these ARE the demo, seed and test them deliberately)

| ID      | Input                                                                                                                                                              | Expected result                                                                                                                                                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **R1**  | CC6.2, Support Engineering, "Monthly access review for support tooling admin accounts was not performed for May to July 2026. No reviewer sign-off exists." No evidence_ref | `possible_recurrence = true`. Related: F-2024-03, F-2023-02. Previous root cause: ownership gap after reorg or departure. Previous remediation: REM-118 marked done with no evidence, then reopened, ineffective. POL-ACCESS v3 (monthly) shown as current, v2 as history. Checks: overdue_test (CC6.2), stale_ticket (REM-118, owner left), missing_evidence |
| **R2**  | CC6.2, Engineering, "A new contractor was granted the production admin role on 2026-08-19 without manager approval." evidence_ref `TCK-8841`                       | `possible_recurrence = false`. Same control as F-2023-02 and F-2024-03, but failure type is "approval bypassed", not "review not performed". Shown as related, not recurrence. **Proves same control_id is not enough**                                    |
| **R1b** | CC6.2, Data Platform, "Monthly access review for the data warehouse admin group was skipped in August 2026." evidence_ref null                                     | **Before confirming R1:** recurrence with root cause "ownership gap". **After confirming R1 with a corrected root cause:** result cites the confirmed memory first, root cause changes, remediation guidance changes, confidence rises. **Proves live learning** |
| **D1**  | CC7.2, Platform, "Quarterly backup restore test was not executed." evidence_ref null                                                                               | Deterministic checks fire (overdue_test, missing_evidence). `possible_recurrence = false`, warning `no_history` for this failure. Proves rules handle the obvious and memory handles history                                                             |

Correction used in the live-learning step (analyst edits R1's suggestion): confirmed root cause = "Access-review ownership was assigned to Security Ops in RACI v1 (2025-03) but only for production infrastructure. Support tooling and other SaaS admin groups were never in scope, so no one owns their reviews." Confirmed remediation = "Add SaaS and tooling admin groups to the access-review inventory, name an owner per group, require dated reviewer sign-off as evidence."

### 5.5 Realism checklist

- [ ] Real-sounding Indian and international employee names, consistent across files
- [ ] Real SOC 2 control IDs (CC6.1, CC6.2, CC7.2, CC8.1, and so on)
- [ ] Believable auditor language ("Management did not provide evidence that...")
- [ ] Dates that make sense (tickets open after findings, not before, policy versions in order)
- [ ] Reorg and departure events that plausibly explain the recurring root cause
- [ ] Mixed severities, not everything "high"

### 5.6 Validation (script, about 15 minutes)

`scripts/validate_data.py` checks: every `finding_id` in remediations exists, dates are ordered, every `supersedes` points to an earlier memory of the same subject, all IDs referenced in memory text exist, R1 and R2 both have at least one same-control past finding, and the decoy (M-010) is resolved with evidence. Then read the whole set once by hand and fix anything that sounds fake.

---

## 6. Phased Build Plan (MVP-first, 11 to 12 hours)

Timings assume **2 people working in parallel** (Member A backend and memory, Member B data and frontend). For a solo build, do the phases in order and cut the UI to the four components in Section 4 with minimal styling. **Order matters more than the exact hours.** Content deliverables (Phase 8) run alongside and are mandatory.

| Phase | Window (hours)  | Goal                                                    |
| ----- | --------------- | ------------------------------------------------------- |
| 0     | 0:00 to 1:00    | Setup and Hindsight hello-world                         |
| 1     | 1:00 to 3:00    | Seed 26 memories                                        |
| 2     | 3:00 to 4:15    | New finding input and recall of relevant history        |
| 3     | 4:15 to 6:15    | Recurrence analysis, past root cause and remediation    |
| 4     | 6:15 to 7:45    | Analyst confirmation, retain, prove changed behavior    |
| 5     | 3:15 to 9:30    | UI flow (mock first, real API from 7:45)                |
| 6     | 9:30 to 10:30   | Hardening and demo rehearsal                            |
| 7     | 10:30 to 11:45  | README, demo script, videos, release                    |
| Buffer | 11:45 to 12:00 | Fixes only. No new work                                 |

### PHASE 0: Setup and Hindsight hello-world (Hours 0 to 1)

**Both together. No other coding before the go/no-go passes.**

- [ ] **T0.1** Register on Hindsight Cloud. Apply promo code **MEMHACK99** in the billing section AFTER registering ($50 credits). Join the Hindsight community Slack for fast answers
- [ ] **T0.2** Create Groq account and API key, test one call with `openai/gpt-oss-120b`
- [ ] **T0.3** Create GitHub repo, MVP folder skeleton from Section 4, `.gitignore` (must include `.env`), `.env.example` with `HINDSIGHT_BASE_URL`, `HINDSIGHT_API_KEY`, `GROQ_API_KEY`, `HINDSIGHT_BANK_ID`, `AUDIT_TODAY` (default `2026-09-28`, keeps deterministic checks repeatable)
- [ ] **T0.4** Read the Hindsight quickstart and Python client page. Paste real API notes into `docs/hindsight-notes.md` (Section 3.3 checklist)
- [ ] **T0.5** `scripts/hello_hindsight.py`: retain 2 memories, recall them, call reflect. **This is the go/no-go check**
- [ ] **T0.6** Verify round trip: do header tokens and IDs survive in recalled text, how long from retain to recall, and how to delete or create a bank. Record results in the notes
- [ ] **T0.7** Freeze schemas (Section 3.6) and API contract (Section 7). Write a short `AGENTS.md` and `SPEC.md` (Section 12), commit

**Exit check:** retain, recall, and reflect return results from a plain script, and you know how to map recalled text back to a `mem_id`. If not, ask in Slack before doing anything else.

---

### PHASE 1: Seed 20 to 30 memories (Hours 1 to 3)

- [ ] **T1.1** *(B)* Write `data/controls.json`, `staff.json`, `findings.json`, `remediations.json`, `control_tests.json`, `memories.json` (26 memories per Section 5.3), and `scenarios.json` (Section 5.4)
- [ ] **T1.2** *(B)* `scripts/validate_data.py` (Section 5.6). Then one manual read-through for realism
- [ ] **T1.3** *(A)* `memory/formatter.py`: turn each record into a memory with the header line and rich paragraph (Section 3.4 rules). Also builds `analyst_confirmation` memories for Phase 4
- [ ] **T1.4** *(A)* `memory/client.py`: thin Hindsight wrapper with retry on transient errors and a clear error object
- [ ] **T1.5** *(A)* `memory/seed.py` and `scripts/seed_memory.py`: retain every memory with correct `timestamp`. Make it **idempotent**: stable document ID per memory if the API supports it **[VERIFY]**, otherwise a fresh bank per seed run
- [ ] **T1.6** Verify in the Hindsight UI that documents and entities appear for the bank
- [ ] **T1.7** `scripts/smoke_test.py`:
  - recall "access review not performed" returns F-2023-02 and F-2024-03 and their root causes
  - recall "contractor admin access without approval" does NOT rank the two review findings above the CC6.2 provisioning context
  - recall "policy access review frequency" returns both POL-ACCESS versions
  - recall "REM-118" returns both the done and reopened states

**Exit check (Phase 1):** the smoke test passes. If recall quality is weak, **improve the memory text (IDs, dates, department, plain-language failure description), not the code.**

---

### PHASE 2: New finding input and recall (Hours 3 to 4:15)

- [ ] **T2.1** *(A)* FastAPI app, CORS for the frontend origin, env config loader, `GET /health`, global exception handler returning `{error, code}`
- [ ] **T2.2** *(A)* `memory/recall.py`: build the 3 recall queries (Section 3.5), run them, dedupe, parse headers into `RecalledMemory`
- [ ] **T2.3** *(A)* `memory/temporal.py`: mark `is_current` and `superseded_by` using `supersedes` then `as_of`. Unit tests: POL-ACCESS v3 current and v2 history, REM-118 reopened state current, a confirmed memory beats a seeded one
- [ ] **T2.4** *(A)* `agent/checks.py`: deterministic overdue test, stale ticket, and missing evidence. Unit tests for each, using `AUDIT_TODAY`
- [ ] **T2.5** *(A)* `POST /analyze-finding` **v0**: validate input, recall, resolve time, run checks, return `memories_used` and `deterministic_checks` (no LLM yet)
- [ ] **T2.6** *(B)* In parallel: scaffold Next.js and Tailwind, `lib/api.ts` typed client from the contract, and a static mock of `AnalyzeFindingResponse` for R1

**Exit check:** `curl` with R1 returns F-2024-03, F-2023-02, their root causes, and REM-118 in `memories_used`, with correct `is_current` flags and the three deterministic checks.

---

### PHASE 3: Recurrence analysis (Hours 4:15 to 6:15)

- [ ] **T3.1** *(A)* `agent/llm.py`: Groq client with:
  - primary `openai/gpt-oss-120b`, fallback `qwen/qwen3-32b`
  - retry with exponential backoff (3 attempts)
  - JSON parse failure handling: strip code fences, re-ask once with "return valid JSON only"
  - function calling error handling (prefer plain JSON output over tool calls)
  - request timeout and a clear error object, not a crash
- [ ] **T3.2** *(A)* `agent/prompts.py`: judge prompt with the five-dimension rubric (Section 3.5), "use only provided memories", "cite memory IDs for every claim", "answer unknown when memory is silent", "current state beats history", "same control ID alone is not evidence of recurrence"
- [ ] **T3.3** *(A)* Reflect step: one advisory `reflect` call with a 10 second timeout, output passed to the judge as labeled synthesized context (not citable as a memory). On failure add warning `reflect_skipped` and continue
- [ ] **T3.4** *(A)* `agent/analyzer.py`: recall, resolve, judge, **guardrails** (Section 3.5 Step 4), then build `related_past_findings`, `previous_root_cause`, `previous_remediation` (from current-state memories), and `explanation`
- [ ] **T3.5** *(A)* `agent/registry.py`: store each analysis as `suspected` with an `analysis_id`. Wire the final `POST /analyze-finding`
- [ ] **T3.6** *(A)* Scenario tests from `scenarios.json`:
  - R1: `possible_recurrence = true`, related includes F-2024-03, previous root cause and remediation populated, all three checks present
  - R2: `possible_recurrence = false`, F-2023-02 and F-2024-03 shown as related with `is_recurrence_candidate = false`
  - D1: checks fire, `possible_recurrence = false`, warning `no_history`
- [ ] **T3.7** *(A)* Edge cases:
  - empty recall: say "no history found", never invent
  - Hindsight unreachable: degrade with a clear message and warning `hindsight_degraded`
  - judge returns malformed JSON: retry, then fallback model
  - unknown or malformed `control_id`: polite validation error
  - judge cites a memory ID that was not recalled: drop that claim

**Exit check (Phase 3):** R1 flags recurrence with the right past root cause and remediation, R2 does not, D1 shows only deterministic checks. Every claim carries memory IDs.

---

### PHASE 4: Confirm, retain, prove changed behavior (Hours 6:15 to 7:45)

- [ ] **T4.1** *(A)* `POST /confirm-finding`: load the suspected analysis, validate the request (root cause required unless `not_recurrence`), build one `analyst_confirmation` memory (plus a linked finding memory for the new finding), retain with `timestamp = now`, `trust = verified`, `supersedes` set if it replaces an earlier state. Poll recall for up to 30 seconds (or use the sync behavior from T0.6) and return `retrievable`
- [ ] **T4.2** *(A)* Trust tests: analysis never calls `retain`, `suspected` content is never present in a retain payload, confirm is the only retain path, rejections are retained as verified memories
- [ ] **T4.3** *(A)* `scripts/learning_check.py` (the changed-behavior proof, runs against a fresh bank from `reset_demo.py`):
  1. **Empty-bank control:** R1 against an empty bank returns `possible_recurrence = false`, warning `no_history`. Shows Hindsight is essential
  2. **Seeded bank:** R1 returns recurrence with the previous root cause and remediation
  3. **Confirm** R1 with the corrected root cause and remediation from Section 5.4
  4. **Analyze R1b:** `memories_used` now includes `M-CONF-0001` first, `previous_root_cause` reflects the confirmed cause, remediation guidance changes, and the result differs from the same R1b run before step 3
  5. **Rejection test:** confirm R2 as `not_recurrence` with a reason, re-run an R2-like finding, and confirm it stays non-recurrence and cites the rejection
- [ ] **T4.4** *(A)* `scripts/reset_demo.py`: create a fresh bank ID, reseed, print the new ID. Reset takes under 2 minutes
- [ ] **T4.5** Record the real before and after outputs of the learning check into `docs/`. Report what actually happened. Do not fabricate improvement

**Exit check (Phase 4):** `learning_check.py` passes from a clean reset, twice in a row. The next query provably changes after the analyst confirms. **This is the MVP.** Everything after this is UI, docs, and demo.

---

### PHASE 5: One MVP UI flow (Hours 3:15 to 9:30, Member B, mock first)

Single page, four stages in order: **New Finding form, Analyze, Recurrence Result, Past Memory Evidence, Confirm or Correct Result.**

- [ ] **T5.1** `NewFindingForm`: fields for control_id, department, finding, optional evidence_ref, an **Analyze** button, and 3 one-click prefills for R1, R2, R1b
- [ ] **T5.2** `RecurrenceResult`: verdict banner ("Possible recurrence" or "Not a recurrence"), confidence, explanation, a permanent **Suspected** badge, previous root cause, previous remediation with outcome, related past findings (recurrence candidates vs "related, not a recurrence"), deterministic check chips
- [ ] **T5.3** `MemoryEvidencePanel`: every memory used, with date, type, trust badge, and **Current** or **History** badge (this is the hero of the memory score). Superseded states are visible but dimmed
- [ ] **T5.4** `ConfirmCorrectPanel`: editable root cause and remediation pre-filled with the suggestion, outcome selector, analyst name, buttons **Confirm recurrence**, **Correct and confirm**, **Not a recurrence**. After submit, show "Retained as verified memory M-CONF-0001"
- [ ] **T5.5** Loading, empty (`no_history`), and error states (Hindsight down, LLM error)
- [ ] **T5.6** *(from 7:45)* Swap the mock for the real API. Run the full flow in the browser without touching the terminal
- [ ] **T5.7** Readability pass for a projector: one accent color, large fonts, no layout jumps between stages

**Exit check:** the full demo flow (R1, R2, confirm, R1b) works end to end in the browser.

---

### PHASE 6: Hardening and rehearsal (Hours 9:30 to 10:30)

- [ ] **T6.1** Run `reset_demo.py`, then the full 3 minute demo, 3 times. Time it. Cut anything that drags
- [ ] **T6.2** Pre-warm the backend and cache a known-good R1 response as an offline fallback fixture
- [ ] **T6.3** Test on the presentation laptop and projector resolution
- [ ] **T6.4** Fix only bugs seen during rehearsal. No new features

---

### PHASE 7: README, docs, and submission (Hours 10:30 to 11:45)

- [ ] **T7.1** Full README (Section 9), with the Hindsight usage section and the learning-check before and after results
- [ ] **T7.2** Architecture diagram to `docs/architecture.png`
- [ ] **T7.3** Write `docs/demo-script.md` (Section 8)
- [ ] **T7.4** Record the **demo video** (screen capture plus voiceover, 2 to 3 minutes)
- [ ] **T7.5** Record a **backup live-demo video** in case Wi-Fi or an API fails on stage
- [ ] **T7.6** Cleanup: remove dead code, run linter and formatter
- [ ] **T7.7** Verify `.env` is not in git history. **Rotate keys if it ever was**
- [ ] **T7.8** Tag a release `v1.0-submission`

---

### PHASE 8: Content deliverables (parallel, start at hour 6, finish by submission)

**Mandatory for EVERY team member.** These do not count against the 11 to 12 hour build clock, but they are not optional. Read the official Hackathon Content Guide first (link is in the original doc).

- [ ] **T8.1** Each member: read the content guide, list their required challenges
- [ ] **T8.2** Each member: write their **Article**
- [ ] **T8.3** Each member: publish their **Social Media post**
- [ ] **T8.4** Each member: record their **Video**
- [ ] **T8.5** Collect all links into one shared doc and into the README
- [ ] **T8.6** Assign ONE person to chase these, since forgetting them is the most common way to lose points

**Content angles worth using (pick different ones per member so the posts do not repeat):**

- "Why audits keep finding the same problems" (problem story)
- "Same control, different failure: why control IDs are not recurrence" (technical)
- "Building an agent that only trusts what the analyst confirmed" (memory safety)
- "How Hindsight retain and recall changed my agent's next answer" (learning)

---

## 7. API Contract (freeze in Phase 0)

Base URL: `http://localhost:8000`

| Method | Path                | Body                             | Returns                                       |
| ------ | ------------------- | -------------------------------- | --------------------------------------------- |
| GET    | `/health`           | none                             | `{ok: true, hindsight: bool, llm: bool}`      |
| POST   | `/analyze-finding`  | `NewFindingRequest`              | `AnalyzeFindingResponse`                      |
| POST   | `/confirm-finding`  | `ConfirmFindingRequest`          | `ConfirmFindingResponse`                      |

### `POST /analyze-finding`

Input:

```json
{
  "control_id": "CC6.2",
  "department": "Support Engineering",
  "finding": "Monthly access review for support tooling admin accounts was not performed for May to July 2026. No reviewer sign-off exists.",
  "evidence_ref": null
}
```

Output (abridged, R1):

```json
{
  "analysis_id": "AN-0007",
  "status": "suspected",
  "possible_recurrence": true,
  "recurrence_confidence": "high",
  "related_past_findings": [
    {
      "finding_id": "F-2024-03",
      "control_id": "CC6.2",
      "department": "Engineering",
      "raised_date": "2024-03-12",
      "summary": "Quarterly production admin access reviews not performed",
      "same_control_id": true,
      "is_recurrence_candidate": true,
      "comparison": {
        "semantic_similarity": {"rating": "match", "reason": "Both describe access reviews not performed with no sign-off"},
        "failure_type": {"rating": "match", "reason": "Review omitted in both cases"},
        "root_cause": {"rating": "partial", "reason": "Prior cause was an ownership gap after reorg; current owner unknown"},
        "org_context": {"rating": "partial", "reason": "Ownership scope changed with Security Ops RACI v1 (M-025)"},
        "remediation": {"rating": "match", "reason": "REM-118 was marked done with no evidence and later reopened"}
      },
      "memory_ids": ["M-004", "M-005", "M-006", "M-007"]
    }
  ],
  "previous_root_cause": {
    "text": "Review duty was not handed over after the Feb 2024 reorg and no backup owner was named.",
    "as_of": "2024-03-25",
    "source_mem_ids": ["M-005"]
  },
  "previous_remediation": {
    "text": "REM-118 was marked done on 2024-06-01 with no evidence and reopened on 2024-11-18. Owner has since left.",
    "outcome": "ineffective",
    "evidence_ref": null,
    "source_mem_ids": ["M-006", "M-007"]
  },
  "explanation": "This looks like a repeat of F-2024-03 (suspected). ...",
  "memories_used": [ { "mem_id": "M-007", "type": "remediation", "trust": "verified", "as_of": "2024-11-18", "is_current": true, "superseded_by": null, "text": "...", "relevance": 0.91 } ],
  "deterministic_checks": [
    {"kind": "overdue_test", "control_id": "CC6.2", "severity": "medium", "explanation": "Last tested 2025-04-15, required every 90 days", "sources": ["M-020"]},
    {"kind": "stale_ticket", "control_id": "CC6.2", "severity": "high", "explanation": "REM-118 open since 2024-11-18, owner left FinPay", "sources": ["M-007", "M-024"]},
    {"kind": "missing_evidence", "control_id": "CC6.2", "severity": "medium", "explanation": "No evidence_ref supplied for the new finding", "sources": []}
  ],
  "warnings": []
}
```

### `POST /confirm-finding`

Input:

```json
{
  "analysis_id": "AN-0007",
  "decision": "correct",
  "linked_finding_ids": ["F-2024-03"],
  "confirmed_root_cause": "Access-review ownership was assigned to Security Ops in RACI v1 (2025-03) but only for production infrastructure. Support tooling and other SaaS admin groups were never in scope, so no one owns their reviews.",
  "confirmed_remediation": "Add SaaS and tooling admin groups to the access-review inventory, name an owner per group, require dated reviewer sign-off as evidence.",
  "outcome": "open",
  "analyst": "Arjun Mehta",
  "note": null
}
```

Output:

```json
{"ok": true, "trust": "verified", "retained_mem_ids": ["M-CONF-0001"], "retrievable": true, "message": "Retained as verified memory. Future analyses will use it."}
```

Rules:

- All errors return `{error: str, code: str}` with a proper HTTP status
- Every claim in a response carries `memory_ids` or `sources` that map to real recalled memories
- No endpoint may return unsourced claims about findings
- `/analyze-finding` never writes to Hindsight. `/confirm-finding` is the only write path
- `status` on an analysis is always `suspected`. Only the confirm response returns `trust: "verified"`

Endpoints from the previous plan (`/readiness`, `/ask`, `/feedback`, `/memory/trace`, `/controls/{id}/timeline`, `/demo/reset`, `/eval/curve`) are **[POST-MVP]** (Section 16).

---

## 8. Demo Script (3 minutes, memorize this)

**Persona voice:** you are narrating Arjun's morning.

| Time          | Beat                     | What is on screen                                                   | What you say                                                                                                                                                                                                                  |
| ------------- | ------------------------ | ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0:00 to 0:20  | Hook                     | Header: "SOC 2 audit in 30 days"                                    | "Arjun's team logs a new finding. Is it new, or is it the same failure they already 'fixed'? Auditors remember. His team doesn't."                                                                                            |
| 0:20 to 1:10  | New finding, recurrence  | Click prefill R1, **Analyze**. Recurrence Result and Memory Evidence | "It recalls F-2024-03 and F-2023-02. Same failure: reviews not performed. Previous root cause: nobody owned it after the reorg. Previous fix, REM-118: marked done, no evidence, later reopened, owner left. The policy is now monthly, quarterly is history." Point at the **Suspected** badge and the memory panel dates |
| 1:10 to 1:40  | Not just control ID      | Prefill R2, **Analyze**                                             | "Same control, CC6.2. But this is an approval bypass, not a missed review. The agent says not a recurrence. Same control ID is not the same failure."                                                                          |
| 1:40 to 2:30  | Live learning            | Back to R1 result. Edit the root cause, click **Correct and confirm** | "Arjun knows better. The real cause: Security Ops owns only production infrastructure, and support tooling was never in scope. He corrects it and confirms. Only now does it become a trusted memory." Show "Retained as M-CONF-0001" |
| 2:30 to 2:50  | Changed behavior         | Prefill R1b, **Analyze**                                            | "A new finding, different team. The confirmed memory is first, the root cause is Arjun's, and the recommended fix changed. It learned from one confirmation."                                                                 |
| 2:50 to 3:00  | Close                    | Result plus memory panel                                            | "AI guesses stay suspected. Only analyst-confirmed facts are remembered. Auditors remember everything you got wrong last year. Now your team does too."                                                                        |

Optional beat if time allows (or use in Q&A): run D1 to show that overdue tests and missing evidence come from simple rules, while recurrence comes from Hindsight memory. Also show the empty-bank run from `learning_check.py` ("without memory there is no verdict").

Demo hygiene:

- Run `scripts/reset_demo.py` before each run and confirm the new bank ID in `.env`
- Pre-warm the backend so the first request is not slow
- Keep the cached R1 response fixture and a screenshot of every stage as a last-resort fallback
- Rehearse the answers to the tough questions below

### Tough judge questions and answers

- **"Is the data real?"** Real SOC 2 control IDs from an open control set. The company history is synthetic, which the hackathon permits. Validated by script for consistency.
- **"How is this different from Vanta or Drata?"** They monitor current control status. We remember history and compare new issues against past failures, root causes, and fixes.
- **"Does the LLM hallucinate findings?"** It only compares against recalled memories, every claim must cite a memory ID, and uncited claims are dropped. Its output is labeled suspected and never stored as fact.
- **"Why not just match on control ID?"** We tested it. R2 has the same control ID as two past findings but a different failure, and the agent correctly says no recurrence.
- **"Why memory and not a database?"** A database returns rows for a control ID. Hindsight recalls by meaning across findings, causes, fixes, and policy history, and it keeps learning from confirmed outcomes.
- **"What if the AI is wrong and you retain it?"** It cannot. Only analyst-confirmed facts are retained. Rejections are retained too, so a false match does not repeat.
- **"What if Hindsight is down?"** The system degrades gracefully, tells the user, and never invents history.
- **"Path to adoption?"** Plug into existing GRC tools and ticketing via connectors. SOC 2 prep is a paid pain point today.

---

## 9. README Outline (Required Deliverable)

- [ ] Title, tagline, and a hero screenshot or GIF
- [ ] **Problem** (3 sentences)
- [ ] **Solution** (3 sentences)
- [ ] **Demo video link** and live demo instructions
- [ ] **How Hindsight memory is used** (REQUIRED section, be specific):
  - what we retain and why (table from Section 3.4), and the trust rule (suspected vs verified)
  - how recall is used and with which queries
  - how temporal handling works (current vs history, `supersedes`)
  - how reflect is used (advisory, timeboxed) and what happens when it is skipped
  - how analyst confirmation is retained and changes the next analysis
  - before and after results from `learning_check.py`, including the empty-bank run
- [ ] Architecture diagram
- [ ] The recurrence rule (Section 3.5) and the R2 "same control is not recurrence" example
- [ ] Data section: sources, what is synthetic, licensing note
- [ ] Setup: prerequisites, env vars, install, seed, run, reset
- [ ] Testing instructions (unit tests, scenario tests, `learning_check.py`)
- [ ] Edge cases and error handling we cover
- [ ] Limitations and roadmap (Section 16)
- [ ] Team members and roles
- [ ] Links to all content deliverables (articles, posts, videos)
- [ ] License and attribution (Vanta control set, Hindsight)

---

## 10. Team Split (2 members, MVP)

|         | Member A: Backend and Memory                                            | Member B: Data and Frontend                                           |
| ------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Phase 0 | Hindsight hello-world, round-trip checks, Groq test                     | Repo, schemas, contract, AGENTS.md and SPEC.md                        |
| Phase 1 | Formatter, client wrapper, seed script, smoke test                      | Author 26 memories and scenarios, validation, realism pass            |
| Phase 2 | FastAPI, recall, temporal resolver, checks, `/analyze-finding` v0       | Scaffold UI and mock                                                  |
| Phase 3 | LLM layer, judge, guardrails, reflect step, scenario tests              | Build the four components against the mock                            |
| Phase 4 | `/confirm-finding`, trust tests, `learning_check.py`, reset script      | Confirm panel, wire to real API from 7:45                             |
| Phase 5 | Support and bug fixing                                                  | Loading, empty, error states, projector polish                        |
| Phase 6 to 7 | Fallback fixture, tests, cleanup, release tag                      | README, demo script, videos                                           |
| Shared  | Demo rehearsals, each member's own content deliverables (Phase 8)       |                                                                       |

Sync every 2 hours (10 minutes). Agree on the contract in the first hour, then work in parallel. Solo build: do A's work first, then B's four components, no polish.

The previous five-member split is **[POST-MVP]** and not needed for 11 to 12 hours.

---

## 11. Risk Register

| Risk                                                      | Likelihood | Impact | Mitigation                                                                                                     |
| --------------------------------------------------------- | ---------- | ------ | -------------------------------------------------------------------------------------------------------------- |
| Hindsight SDK usage differs from assumptions              | Medium     | High   | T0.5 and T0.6 go/no-go, notes in `docs/hindsight-notes.md`, ask in Slack                                       |
| Retain is async, so the confirmed memory is not recalled yet | Medium  | High   | Measure in T0.6, poll in T4.1, show `retrievable`, wait before the R1b step in the demo                        |
| Hindsight rewrites text and header tokens are lost        | Medium     | High   | Check in T0.6. Fallback: map by `document_id` or metadata                                                      |
| Recall returns noisy results for short findings           | Medium     | High   | Three query variants, richer memory text with IDs, dates, departments, plain-language failure descriptions      |
| Judge marks same-control findings as recurrence           | Medium     | High   | Rubric plus code guardrail (failure type must match), R2 scenario test                                         |
| Reflect is slow or vague                                  | Medium     | Low    | It is advisory and timeboxed to 10 seconds. Skip on failure                                                    |
| Groq function calling errors                              | High       | Medium | Retry, fallback model, JSON repair, plain JSON output instead of tool calls                                    |
| Groq rate limits mid-demo                                 | Medium     | High   | Cached R1 fixture, fallback model, backup video                                                                |
| Synthetic data feels fake                                 | Medium     | High   | Manual realism pass, checklist in 5.5                                                                          |
| Agent hallucinated SDK calls (Antigravity)                | High       | Medium | Paste real docs into `docs/`, verify Hindsight calls by hand                                                   |
| Live demo Wi-Fi failure                                   | Medium     | High   | Backup video, cached response, screenshots                                                                     |
| Forgetting content deliverables                           | High       | High   | One owner, deadline before submission, checklist T8.x                                                          |
| Secrets leaked to GitHub                                  | Low        | High   | `.gitignore`, `.env.example`, check history before submit                                                      |
| Scope creep (readiness score, charts, more endpoints)     | High       | High   | Non-goals list in 2.5, everything else lives in Section 16 and is not built                                    |

---

## 12. Antigravity Workflow

### 12.1 Files to write BEFORE dispatching any agent (30 minutes total, inside Phase 0)

**AGENTS.md** must contain:

- Stack and versions
- Folder structure from Section 4
- Schemas from Section 3.6
- API contract from Section 7
- Rules: every claim must carry a memory ID, never invent history, handle empty recall, never commit secrets, `/analyze-finding` never retains, only `/confirm-finding` retains, same `control_id` alone is never recurrence, write tests for checks, temporal resolver, and guardrails
- Hindsight rules: use only methods in `docs/hindsight-notes.md`, never guess SDK signatures

**SPEC.md** must contain:

- Pitch line, MVP goal, and persona
- The workflow in Section 2.3
- Scenarios R1, R2, R1b, D1
- The 3-minute demo script
- Definition of done per phase (the exit checks above)

### 12.2 Agent dispatch order

| Order | Agent    | Task                                                          | Mode     |
| ----- | -------- | ------------------------------------------------------------- | -------- |
| 1     | Memory   | Formatter, wrapper, seed, smoke test (Phase 1)                | Planning |
| 2     | Backend  | Phase 2 and Phase 3 tasks, one at a time                      | Planning |
| 3a    | Backend  | Phase 4 confirm, trust tests, learning check                  | Planning |
| 3b    | Frontend | Phase 5 components (parallel with 2 and 3 after contract freeze) | Planning |
| 4     | Docs     | README first draft                                            | Fast     |

Data authoring (Phase 1, T1.1) is done by a human, with an LLM only for drafting text.

### 12.3 Review discipline

- Read every implementation plan before approving
- Run the code yourself after each agent finishes
- Verify every Hindsight call against the real docs
- Commit after every working step
- Never let two agents edit the same files at once
- Keep the terminal policy on "ask" for anything risky
- Never paste API keys into prompts

---

## 13. Definition of Done (Submission Checklist)

**Product (MVP)**

- [ ] Hindsight hello-world passes and notes are in `docs/hindsight-notes.md`
- [ ] 26 memories seeded, smoke test passes
- [ ] `POST /analyze-finding` accepts `control_id`, `department`, `finding`, optional `evidence_ref`
- [ ] Response includes `possible_recurrence`, related past findings, previous root cause, previous remediation, explanation, and memories used
- [ ] R1 flagged as possible recurrence with correct sources
- [ ] R2 (same control, different failure) is NOT flagged as recurrence
- [ ] Overdue test, stale ticket, and missing evidence come from deterministic rules. Recurrence comes from Hindsight memory
- [ ] AI output is labeled `suspected`. Nothing is retained during analysis (test passes)
- [ ] `POST /confirm-finding` retains the analyst-confirmed outcome as a verified memory
- [ ] Temporal handling works: newest verified state is current, older states shown as history
- [ ] `learning_check.py` passes: R1b result changes after confirmation, and the empty-bank run returns `no_history`
- [ ] UI flow works end to end: New Finding, Analyze, Recurrence Result, Past Memory Evidence, Confirm or Correct
- [ ] `reset_demo.py` returns to the seeded state in under 2 minutes
- [ ] Errors handled: Hindsight down, LLM malformed output, empty recall, unknown control ID

**Submission**

- [ ] GitHub repo public, clean, documented
- [ ] README has the Hindsight usage section
- [ ] Demo video recorded and linked
- [ ] Backup demo video recorded
- [ ] Live demo rehearsed at least 3 times
- [ ] All members: Article done
- [ ] All members: Social post published
- [ ] All members: Video recorded
- [ ] No secrets in git history
- [ ] Release tag created

---

## 14. Time Budget Cheat Sheet (11 to 12 hours)

| Block                                        | Share of effort | Calendar window |
| -------------------------------------------- | --------------- | --------------- |
| Setup and Hindsight hello-world              | 8%              | 0:00 to 1:00    |
| Seed 26 memories                             | 17%             | 1:00 to 3:00    |
| New finding input and recall                 | 10%             | 3:00 to 4:15    |
| Recurrence analysis                          | 17%             | 4:15 to 6:15    |
| Confirm, retain, prove changed behavior      | 13%             | 6:15 to 7:45    |
| UI flow (parallel with 2 to 4)               | 17%             | 3:15 to 9:30    |
| Hardening and rehearsal                      | 8%              | 9:30 to 10:30   |
| README, docs, videos, release                | 10%             | 10:30 to 11:45  |
| Buffer                                       | -               | 11:45 to 12:00  |

Content deliverables (Phase 8) run in parallel and are mandatory, but are outside this clock.

**If you fall behind, cut in this order:**

1. The reflect step (recall alone is enough)
2. The `not_recurrence` rejection test and the D1 optional demo beat
3. Prefill buttons and projector polish
4. Stale-ticket chip in the UI (keep it in the API)
5. **Never cut:** seeded memories, `/analyze-finding`, recall evidence panel, the recurrence guardrail (R2), analyst confirmation, retain of confirmed outcome, the changed-behavior proof, README Hindsight section, content deliverables

---

## 15. Success Criteria In One Paragraph

We win if a judge watches 3 minutes and can say: the agent recalled a past finding and correctly saw it was the same failure, not just the same control, it showed the previous root cause and the fix that did not work, it cited exactly which dated memories proved that, it labeled its own guess as suspected, and after the analyst confirmed a corrected root cause it answered the next similar finding differently. In numbers: R1 is flagged, R2 is not, D1 shows only deterministic checks, the empty-bank run returns no history, nothing is retained without analyst confirmation, and `learning_check.py` shows a measurable change in the R1b result after confirmation. Everything in this plan exists to make that sentence true.

---

## 16. Post-MVP / Stretch (NOT built in the 11 to 12 hour window)

Moved out of the MVP. Do not start any of these until the Definition of Done in Section 13 is fully checked.

**Product features**

- [POST-MVP] Readiness score (0 to 100) and `ReadinessGauge`
- [POST-MVP] Predicted findings for the coming audit using Hindsight reflect across years, with likelihood and reasoning
- [POST-MVP] `GET /readiness`, `POST /ask` (free-text Q&A), and `AskBox`
- [POST-MVP] Original flag feedback loop (`POST /feedback`, resolved or false alarm on flags) and `FeedbackButtons`. The MVP replaces this with `/confirm-finding`
- [POST-MVP] Sync structured records after analyst confirmation, so overdue, stale, and missing-evidence checks also reflect confirmed outcomes
- [STRETCH] Memory ON/OFF toggle in the UI (the MVP proves essentiality with the empty-bank run instead)
- [STRETCH] Auditor question simulator ("show evidence of Q2 access review")
- [STRETCH] Cross-control recurrence scenario R3 (different control ID, same root cause, for example vendor review ownership gap vs access review ownership gap)

**Visuals and UX**

- [POST-MVP] 3-year `ControlTimeline` (Recharts)
- [POST-MVP] Learning curve chart and `eval_learning_curve.py` with 8 to 12 scripted interactions
- [POST-MVP] Header with audit countdown, three-panel dashboard layout
- [POST-MVP] SSE progress streaming ("Recalling history...", "Comparing with past findings...")
- [POST-MVP] Mobile-safe layout

**API and infra**

- [POST-MVP] `GET /memory/trace`, `GET /controls/{id}/timeline`, `POST /demo/reset` (the MVP uses `scripts/reset_demo.py`), `GET /eval/curve`
- [POST-MVP] Real ticketing and GRC integrations, authentication, more frameworks (ISO 27001)

**Data and process**

- [POST-MVP] `generate_data.py` LLM synthetic data generator and more than 10 controls
- [POST-MVP] Full Vanta control set import, NIST OSCAL cross-check
- [POST-MVP] Five-member team split and daily syncs
