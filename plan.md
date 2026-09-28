# MVP-PLAN.md: AuditMemory (Compliance and Audit Agent With Hindsight Memory)

> Hackathon: AI Agents That Learn Using Hindsight.
> Pitch: **"Auditors remember everything you got wrong last year. Your team doesn't. We fix that."**
> This file is the single source of truth for the MVP. Anything not in Sections 1 to 10 is out of scope until the MVP exit check passes (Section 11 is the backlog).

---

## 0. How To Work

- Build phases in order, one task at a time. Tick the box, run the exit check, commit.
- Do not wire the frontend to the backend until the Phase 2 exit check passes. A UI shell against mock JSON may start after Phase 0.
- **[VERIFY]** marks things agents commonly get wrong. Check by hand against the real docs.
- **Never guess SDK signatures.** Use `backend/docs/hindsight-notes.md`. If something is missing there, run a tiny script to inspect the real object, write the result into the notes, then code.
- Never let two agents edit the same files at once. Never paste API keys into prompts. Terminal policy: ask for anything risky.

---

## 1. MVP Scope

**Product:** an agent that remembers FinPay's audit history, uses it to flag what the next auditor will catch, predicts likely findings, and changes its answers when the user gives feedback.

**Fixed scenario (do not change):**

- Company FinPay (fictional fintech, 120 people). Persona: Arjun Mehta, Compliance Manager.
- SOC 2 Type II audit starts in 30 days. Scope: Security, plus one Availability control (A1.3, backup restore test).
- History: audit cycles 2023, 2024, 2025, plus current-year control tests.
- **`AS_OF_DATE = 2026-09-28`** is a config constant. `AUDIT_START = AS_OF_DATE + 30 days`. Never call `date.today()` anywhere, or the seeded traps drift and stop being traps.

**MVP capabilities (all must work):**

1. **Memory ON/OFF toggle.** OFF means the agent has no access to any company history (neither Hindsight nor the JSON files) and gives generic advice.
2. **Detect** four seeded problems and NOT flag one decoy.
3. **Predict** likely findings for the coming audit, with reasoning and sources.
4. **Learn:** feedback (resolved with evidence, false alarm, still open) changes the score, the explanation, and the predictions.
5. **Memory panel:** the recalled memories (with dates) behind every flag and answer.

**Non-goals (say no):** live integrations, frameworks beyond SOC 2, auth or accounts, document upload, model training, database, SSE streaming, timeline chart, learning-curve eval, auditor simulator, mobile layout.

---

## 2. Architecture and Stack

```
Next.js single page --REST--> FastAPI --> Hindsight Cloud (retain / recall / reflect)
                                     --> Groq LLM (JSON output, NO tool calling)
                                     --> backend/data/*.json (seed) + backend/state/ (feedback, cache)
```

| Layer    | Choice                                                                                                              |
| -------- | ------------------------------------------------------------------------------------------------------------------- |
| Frontend | Next.js, TypeScript, Tailwind. Types generated from FastAPI `/openapi.json` (`openapi-typescript`), not hand-copied |
| Backend  | Python 3.11+, FastAPI, Pydantic v2                                                                                  |
| Memory   | Hindsight Cloud, `hindsight-client` Python SDK                                                                      |
| LLM      | Groq. Primary `openai/gpt-oss-120b`. Fallback `qwen/qwen3.6-27b` **[VERIFY]**                                       |
| Data     | JSON seed files, plus `backend/state/feedback.json` and `backend/state/cache.json` (gitignored)                     |

**LLM model warning:** Groq shut down `qwen/qwen3-32b` on 2026-07-17 (and `llama-3.3-70b-versatile` on 2026-08-16). Read primary and fallback from env (`LLM_PRIMARY_MODEL`, `LLM_FALLBACK_MODEL`) and check them against Groq's live model list at startup. Fail loudly if either is missing.

---

## 3. Hindsight API Surface **[VERIFY]**

Confirmed against the Hindsight Python client docs. Re-check before coding and paste the real notes into `backend/docs/hindsight-notes.md`.

```python
from datetime import datetime
from hindsight_client import Hindsight

client = Hindsight(base_url=BASE_URL, api_key=API_KEY, timeout=30.0)  # Cloud needs api_key

client.banks.create(bank_id="finpay-audit", name="FinPay Audit")       # some docs show client.create_bank(...)
client.retain(bank_id="finpay-audit", content="...", context="audit finding",
              timestamp=datetime(2024, 3, 12), document_id="F-2024-03",
              retain_async=False)                                       # True = background processing
client.retain_batch(bank_id="finpay-audit", items=[{...}, ...])
res = client.recall(bank_id="finpay-audit", query="access review findings")
for r in res.results: print(r.text)
ans = client.reflect(bank_id="finpay-audit", query="What findings tend to recur and why?")
print(ans.text)
```

Things to confirm by inspection and record in the notes:

- `timestamp` type: docs show a `datetime`, the README shows an ISO string. Use whichever the installed SDK accepts.
- Which fields a recall hit really has (id, date, document_id, score). The wrapper normalizes hits to `MemoryHit{id, text, date?, relevance?}`. Make `relevance` optional in the UI.
- Whether re-retaining the same `document_id` upserts (idempotent seeding) and whether documents can be deleted.
- Whether a client with async methods exists. If the client is sync, all FastAPI routes must be plain `def` (never blocking calls inside `async def`).
- Retain uses an LLM to extract facts, so it is slow (seconds per record) and may drop or reword IDs. Seeding is a one-time step and is never part of `/demo/reset`. A memory retained with `retain_async=True` may not be recallable immediately, so never depend on instant recall of fresh feedback.
- Error codes seen in the docs: 401 bad key, 402 out of credits, 404 unknown bank, 400 bad request. The wrapper maps these to clear errors.
- Promo: apply code `MEMHACK99` in billing AFTER registering ($50 credit).

---

## 4. Memory Design (25 percent of the score)

**One bank:** `finpay-audit`. One record per retain call. `document_id` = the record ID. `timestamp` = the record's date.

| Memory type         | Example content                                                                                                                                                                   | Context tag     |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| Audit finding       | "On 2024-03-12 the SOC 2 auditor raised finding F-2024-03 against control CC6.2 (user access reviews): quarterly access reviews were not performed. Severity: high."              | `audit finding` |
| Remediation ticket  | "Ticket REM-118 opened 2024-03-20, owner Priya Nair, to fix F-2024-03 on control CC6.2. Marked done 2024-06-01. Evidence: EV-311 (review checklist). Status: done, not verified." | `remediation`   |
| Control test        | "Control A1.3 (backup restore test) was last tested 2025-07-28 by Rahul Iyer. Result: passed. Policy requires testing every 365 days."                                            | `control test`  |
| Policy or org event | "On 2024-02-10 the platform team was reorganized and three admins left." / "On 2026-01-15 Priya Nair left FinPay."                                                                | `org event`     |
| User feedback       | "On 2026-09-28 Arjun marked flag repeat_finding:CC6.2 as resolved with evidence EV-902. [session S1]"                                                                             | `user feedback` |

**Writing rules:** always include date, control ID, control name in plain words (so "access reviews" matches CC6.2), record ID, owner, status. IDs come early in the text. Use fixed formats: `F-YYYY-NN`, `REM-NNN`, `EV-NNN`, `CC6.2`.

**How each operation is used (this text goes in the README):**

- **Retain:** loads the history and every user feedback event.
- **Recall:** pulls the relevant memories for each flagged control and for each question. These are shown in the memory panel.
- **Reflect:** finds cross-year patterns (for example access findings follow team turnover) and feeds the predictions.

**Why the toggle is honest:** detection uses rules over structured records for precision, and Hindsight supplies the evidence, the cross-year patterns, and the feedback memory. With the toggle OFF, the agent gets none of it.

---

## 5. Data Model and Logic

### 5.1 Schemas (Pydantic is the source of truth)

```python
Severity = Literal["low", "medium", "high"]

class Staff(BaseModel):        name: str; active: bool; departed_date: date | None
class Finding(BaseModel):      id: str; control_id: str; control_name: str; severity: Severity
                               raised_date: date; audit_cycle: int; auditor_note: str   # audit_cycle == raised_date.year
class Remediation(BaseModel):  id: str; finding_id: str; owner: str; opened_date: date
                               marked_done_date: date | None; evidence_ref: str | None
                               status: Literal["open", "done", "verified"]
class ControlTest(BaseModel):  control_id: str; last_tested: date; tester: str
                               result: Literal["passed", "failed", "partial"]; required_frequency_days: int

class MemoryHit(BaseModel):    id: str; text: str; date: date | None; relevance: float | None
class Flag(BaseModel):
    id: str                    # f"{kind}:{control_id}", e.g. "repeat_finding:CC6.2"
    kind: Literal["repeat_finding", "overdue_test", "stale_ticket", "done_no_evidence"]
    control_id: str; severity: Severity; explanation: str
    sources: list[str]         # record IDs that exist in the data (F-, REM-, EV-, control IDs)
    memories: list[MemoryHit]  # recalled from Hindsight
    state: Literal["open", "resolved", "false_alarm"]
    state_note: str | None     # e.g. "Closed on 2026-09-28 with evidence EV-902"
class Prediction(BaseModel):   control_id: str; likelihood: Severity; reasoning: str; sources: list[str]
class ReadinessReport(BaseModel):
    as_of: date; audit_start: date; score: int          # 0 to 100
    score_breakdown: list[dict]                         # [{flag_id, points}] for the tooltip
    flags: list[Flag]; predictions: list[Prediction]; priority_actions: list[str]
```

### 5.2 Detection rules (`detect.py`, deterministic, uses `AS_OF_DATE`, no LLM)

| Kind               | Rule                                                                                                            |
| ------------------ | --------------------------------------------------------------------------------------------------------------- |
| `repeat_finding`   | Control has findings in 2 or more distinct audit cycles AND its latest finding's remediation is not `verified`. |
| `overdue_test`     | `(AS_OF_DATE - last_tested).days > required_frequency_days`                                                     |
| `stale_ticket`     | Remediation `status == open` AND (open more than 180 days OR owner is not active in `backend/data/staff.json`)  |
| `done_no_evidence` | Remediation `status == done` AND `evidence_ref is None`                                                         |

One flag per (kind, control). Flag severity comes from the linked finding; `overdue_test` defaults to medium.

### 5.3 Score (`readiness.py`)

Start at 100, subtract `kind_weight x severity_multiplier` for each **open** flag only, clamp to 0..100, round to int.

- Kind weights: repeat_finding 15, done_no_evidence 12, stale_ticket 8, overdue_test 6.
- Severity multipliers: high 1.0, medium 0.7, low 0.4.
- Return `score_breakdown` so the UI tooltip can show the formula. Never hardcode demo scores; they come from the formula.

### 5.4 Feedback loop

`POST /feedback {flag_id, action, evidence_ref?, note?}`:

- `resolved` **requires** `evidence_ref` (else 400; resolving without evidence would just recreate trap D).
- `false_alarm` removes the penalty. `still_open` reverts an earlier resolve or false alarm. Unknown `flag_id` gives 404.
- `backend/state/feedback.json` is authoritative for the instant score change. Also retain the event to Hindsight (`retain_async=True`, tag `user feedback`, `document_id` `FB-<session>-<n>`, session tag in the text).
- The response explanation is a template (no LLM): "Closed on 2026-09-28 with evidence EV-902. Score 59 to 66 (+7)."
- Predictions react by rule: a resolved control's likelihood drops one level and the reasoning cites the feedback; a false-alarm control's prediction is removed.
- `/demo/reset` clears `backend/state/feedback.json` and bumps the session ID. Recall hits from earlier sessions are filtered out by the wrapper (or deleted by `document_id` if the API supports it). It does NOT reseed Hindsight.

### 5.5 Performance rule

Evidence recall, reflect, and prediction LLM calls are slow. Run them once, save to `backend/state/cache.json`, and reuse. Feedback only re-applies state and recomputes the score, so it returns instantly. The cache also serves as the offline fallback if Hindsight or Groq is down mid-demo. A missing cache is rebuilt lazily on the first `/readiness` call; pre-warm it before demos.

---

## 6. Data Plan (realistic data is the number one thing judges notice)

### 6.1 Volume and sources

- `backend/data/controls.json`: about 12 controls, **hand-written** with real SOC 2 IDs (CC6.1, CC6.2, CC7.1, CC8.1, CC9.2, A1.3, and so on) and your own descriptions (AICPA text is copyrighted). Do not depend on any external control set.
- Verify each ID and name against a real SOC 2 control list. Example of a bug in an earlier draft: CC7.2 is anomaly monitoring, not backups. Backup restore testing belongs to A1.3.
- `backend/data/findings.json` 12 to 16, `backend/data/remediations.json` 10 to 14, `backend/data/control_tests.json` about 12, `backend/data/staff.json` about 15 (at least 3 departed), `backend/data/policy_changes.json` 3 to 4, `backend/data/org_events.json` 3.
- Quality beats quantity. Reflect needs enough cross-year signal for one story: reorg, then departed admins, then access findings recur.

### 6.2 The four traps and the decoy (hand-write these records; compute dates from `AS_OF_DATE`)

Each trap lives on a different control so flags do not overlap.

| Trap                            | Control | Seed                                                                                                                                                                                           | Expected flag ID         |
| ------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| **A: Repeat finding**           | CC6.2   | Access review finding in 2023 (fixed) and again 2024-03. Reorg 2024-02 removed 3 admins. Latest ticket REM-118 `done` with evidence but never `verified`. Policy v3 (monthly reviews) 2024-09. | `repeat_finding:CC6.2`   |
| **B: Overdue test**             | A1.3    | Backup restore test last run `AS_OF_DATE - 427 days`, frequency 365 (overdue by 62 days)                                                                                                       | `overdue_test:A1.3`      |
| **C: Stale ticket**             | CC9.2   | Vendor risk finding 2025-11. Ticket opened `AS_OF_DATE - 270 days`, still `open`, owner departed 2026-01-15 per `backend/data/staff.json`                                                      | `stale_ticket:CC9.2`     |
| **D: Done with no evidence**    | CC7.1   | Vulnerability management finding in 2025. Ticket `done`, `marked_done_date` set, `evidence_ref = null`                                                                                         | `done_no_evidence:CC7.1` |
| **Decoy (must NOT be flagged)** | CC8.1   | High severity change management findings in 2023 AND 2024 (looks like a repeat), but the latest ticket is `verified` with evidence and the 2025 retest passed                                  | none                     |

### 6.3 Generation approach

1. Hand-write trap, decoy, and `backend/data/staff.json` records first.
2. LLM generates only the background records and auditor prose, as hard-constrained JSON. Background records must be clean: tickets verified or done with evidence, tests inside their frequency, no other multi-cycle unverified controls.
3. `validate_data.py` (T1.4) checks the data. The rule engine check (exactly four flags) runs in the T2.2 tests.
4. A human reads the whole dataset once.

**Realism checklist:** consistent employee names across files (mix of Indian and international names), believable auditor language ("Management did not provide evidence that..."), tickets always open after their finding, mixed severities, departures and reorgs that plausibly explain the recurrences.

---

## 7. API Contract (freeze in Phase 0)

Base URL `http://localhost:8000`. CORS allows `http://localhost:3000`. Frontend reads `NEXT_PUBLIC_API_URL`.

| Method | Path          | Body                                                                                                  | Returns                                                                           |
| ------ | ------------- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| GET    | `/health`     | none                                                                                                  | `{ok, hindsight: bool, llm: bool}`                                                |
| GET    | `/readiness`  | none                                                                                                  | `ReadinessReport` (always memory-backed; the UI hides it when toggle OFF)         |
| POST   | `/ask`        | `{question: str, use_memory: bool}`                                                                   | `{answer: str, sources: list[str], memories: list[MemoryHit], used_memory: bool}` |
| POST   | `/feedback`   | `{flag_id: str, action: "resolved" \| "false_alarm" \| "still_open", evidence_ref?: str, note?: str}` | `{ok: true, new_score: int, explanation: str}`                                    |
| POST   | `/demo/reset` | none                                                                                                  | `{ok: true}`                                                                      |

Rules:

- All errors return `{error: str, code: str}` with a proper HTTP status. Codes: `bad_request`, `not_found`, `hindsight_unavailable`, `hindsight_credits`, `llm_failed`.
- Every flag, prediction, and answer carries `sources` that map to real record IDs. Sources not found in the record index are dropped. A memory-ON answer with no valid source becomes "No supporting history found."
- `/ask` with `use_memory=true`: recall on the question, plus the current open flags as context, then the LLM. With `use_memory=false`: LLM only, no records, `sources=[]`, `memories=[]`, and it says it has no company history.

---

## 8. Build Phases

### Phase 0: Setup

- [x] **T0.1** Human: create Hindsight Cloud and Groq accounts and keys, apply the promo code (Section 3)
- [x] **T0.2** Repo skeleton (`backend/`, `frontend/`, `backend/data/`, `backend/scripts/`, `backend/docs/`, `backend/state/`), `.gitignore` with `.env` and `backend/state/`, `.env.example` with `HINDSIGHT_BASE_URL`, `HINDSIGHT_API_KEY`, `HINDSIGHT_BANK_ID`, `GROQ_API_KEY`, `LLM_PRIMARY_MODEL`, `LLM_FALLBACK_MODEL`, `AS_OF_DATE`, `NEXT_PUBLIC_API_URL`
- [x] **T0.3** Hindsight hello-world script (create bank, retain, recall, reflect). Print the raw result objects and write everything learned into `backend/docs/hindsight-notes.md`. **This is the go/no-go check.**
- [x] **T0.4** Groq hello-world: list models, confirm both configured models exist, one JSON-output call with each
- [ ] **T0.5** Freeze schemas (5.1) and contract (Section 7). Copy the rules from Section 9 into `AGENTS.md` and commit

**Exit:** retain, recall, and reflect all return results on Cloud, and both Groq models respond. If Hindsight does not work, stop and ask in the Hindsight Slack.

### Phase 1: Data and Memory Loop

- [ ] **T1.1** `backend/data/backend/data/controls.json` (Section 6.1)
- [ ] **T1.2** Hand-write trap, decoy, and staff records (Section 6.2)
- [ ] **T1.3** `backend/scripts/generate_data.py`: background records and prose via LLM, merged with the hand-written ones
- [ ] **T1.4** `backend/scripts/validate_data.py`: references valid, dates ordered (ticket after finding, done after opened), `audit_cycle == raised_date.year`, ID formats, all traps and the decoy present
- [x] **T1.5** Human read-through and fixes
- [x] **T1.6** `backend/memory/formatter.py`: record to memory text (Section 4 rules)
- [x] **T1.7** `backend/memory/client.py`: thin wrapper with retry on transient errors, 401/402/404 mapped to clear errors, hits normalized to `MemoryHit`, session filter for feedback memories
- [x] **T1.8** `backend/memory/seed.py` and `backend/scripts/seed_memory.py`: create bank, retain every record synchronously with `document_id` and timestamp. Idempotent via `document_id` upsert if verified, otherwise delete and recreate the bank. Also retain staff departures.
- [x] **T1.9** `backend/scripts/smoke_test.py`. Recall results must contain these record IDs somewhere in the top 10:
  - "access review findings" returns both CC6.2 findings (2023 and 2024)
  - "backup restore test" returns the A1.3 test
  - "vendor risk ticket" returns the CC9.2 ticket
  - reflect "What findings tend to recur and why?" mentions access reviews
  - If IDs were dropped by Hindsight's extraction, fix the memory text (IDs earlier, repeated), not the code.

**Exit:** validation and smoke test pass. Reflect gives a sensible cross-year insight (human check).

### Phase 2: Agent Brain

- [x] **T2.1** `backend/agent/llm.py`: Groq client, JSON output validated with Pydantic, **no tool calling**. Exponential backoff (3 attempts) on 429/5xx, 30s timeout. On JSON parse failure: strip code fences, re-ask once with "return valid JSON only", then the fallback model, then return a clear error object (never crash).
- [x] **T2.2** `backend/agent/detect.py` (Section 5.2) plus unit tests: each trap, the decoy, edge cases, and an integration test that `detect()` over the real seed data returns **exactly** the four trap flag IDs and nothing else
- [x] **T2.3** `backend/agent/readiness.py` (Section 5.3) plus tests
- [x] **T2.4** `backend/agent/prompts.py`: force citations ("every claim must cite a source ID; if none, say you do not know"). _(Note: Updated PREDICT_SYSTEM_PROMPT with explicit JSON keys to resolve Pydantic validation errors)._
- [x] **T2.5** `backend/agent/predict.py`: per flagged control, recall related history and attach as `Flag.memories`. One reflect call for cross-year patterns. The LLM builds `Prediction` objects from recalled memories plus the reflect text. Drop predictions with no valid source.
- [x] **T2.6** `backend/agent/state.py`: feedback state, overlay onto the report, and the reset logic (Section 5.4), plus tests
- [x] **T2.7** `backend/agent/ask.py`: memory ON and OFF behavior (Section 7)
- [x] **T2.8** `backend/state/cache.json` build and load (Section 5.5). _(Note: Added utf-8 encoding to cache.py to fix UnicodeEncodeError)._
- [x] **T2.9** Edge cases: empty recall says "no history found" and never invents; Hindsight unreachable returns a clear error and the cached report if present; malformed LLM JSON follows T2.1; unknown control ID in a question gets a polite answer
- [x] **T2.10** `backend/scripts/phase2_check.py` (the exit check below, automated)
  - _(Note: Fixed imports across all agent scripts to drop 'backend.' prefix, ensuring correct resolution when run from the backend directory)_

**Exit:** with memory ON the report has exactly the four expected open flags, each with valid sources and recalled memories, and no decoy flag. With memory OFF, `/ask` returns generic advice with empty sources. After `resolved` on `repeat_finding:CC6.2` with an evidence ID, the score rises, the explanation cites the evidence and date, and the CC6.2 prediction drops. `false_alarm` removes a penalty. Reset restores the original score.

### Phase 3: API Layer

- [x] **T3.1** FastAPI app, CORS, config loader (`AS_OF_DATE` and models from env), global exception handler returning `{error, code}`
- [x] **T3.2** Implement all Section 7 endpoints (plain `def` routes if the client is sync)
- [x] **T3.3** Integration tests hitting every route, including error paths

**Exit:** every route works via curl with the right JSON shapes. `/demo/reset` returns instantly. `/openapi.json` generates the frontend types.

### Phase 4: Frontend (single page, desktop first, big fonts for a projector)

- [x] **T4.1** Scaffold Next.js and Tailwind. Generate types with `openapi-typescript`. Write `frontend/lib/api.ts`.
- [x] **T4.2** Layout: header (company, audit countdown from `audit_start`, `MemoryToggle`), left `ReadinessGauge` with tooltip from `score_breakdown`, center flags, predictions, and `AskBox`, right `MemoryPanel`
- [x] **T4.3** `ReadinessGauge`: score 0 to 100 with color bands
- [x] **T4.4** `FlagList`: card per open flag with kind badge, severity, explanation, clickable source chips. Closed flags in a collapsed section showing `state_note`.
- [x] **T4.5** `MemoryPanel`: recalled memories with dates behind the selected flag or last answer. **This is the hero of the memory score.**
- [x] **T4.6** `MemoryToggle`: big and obvious. OFF hides flags, predictions, and the memory panel ("No company history available") and sends `use_memory=false` to `/ask`.
- [x] **T4.7** `AskBox`: text box with 3 suggested prompts (non-streaming, spinner)
- [x] **T4.8** `FeedbackButtons` on each flag: Resolved (evidence field required), False alarm, Still open. Score updates from the response.
- [x] **T4.9** Predictions section: likelihood chips, reasoning, source chips
- [x] **T4.10** Loading, empty, and error states everywhere. One accent color.

**Exit:** the full demo flow (Section 10) works in the browser without touching the terminal.

### Phase 5: Submission Essentials

- [x] **T5.1** README with a specific "How Hindsight memory is used" section (Section 4 text, the memory table, recall queries, reflect use, feedback retention, memory ON vs OFF screenshots), setup, seed, run, reset, tests, limitations, data sources (real SOC 2 IDs, synthetic history)
- [x] **T5.2** Run the demo 3 times with `/demo/reset` before each. Cut anything that drags.
- [x] **T5.3** Confirm `backend/state/cache.json` fallback works with the network off
- [x] **T5.4** Check no secrets in git history (rotate keys if any were committed), clean repo, tag `v1.0-mvp`

**Human-only deliverables (not agent work, do not forget):** demo video, backup demo video, and per team member an Article, a Social post, and a Video from the official content guide.

---

## 9. Rules For AGENTS.md (copy verbatim)

- Stack: Python 3.11+, FastAPI, Pydantic v2, `hindsight-client`, Groq, Next.js, TypeScript, Tailwind.
- Use only Hindsight methods documented in `backend/docs/hindsight-notes.md`. Never guess signatures.
- Never call `date.today()` or `datetime.now()` for business logic. Use `AS_OF_DATE` from config.
- Every flag, prediction, and answer must carry source IDs that exist in the record index. Drop anything unsourced.
- Never invent history. Empty recall means say "no history found".
- Groq: JSON output plus Pydantic validation. No function or tool calling.
- Never commit secrets or print API keys. `.env` and `backend/state/` stay gitignored.
- Write tests for detection, scoring, and feedback logic.
- Stay inside the MVP scope. Do not add backlog items.

---

## 10. Demo Flow (about 3 minutes; run `/demo/reset` and pre-warm first)

1. **Hook:** header shows "SOC 2 audit in 30 days". "Arjun has 30 days and no idea if FinPay will pass. Auditors remember every mistake from last year. His team doesn't."
2. **Memory OFF:** ask "Are we ready?" and the answer is generic advice with no sources. "Useless."
3. **Memory ON:** the readiness score appears with four flags. Click a source chip on each to show the exact memory in the panel.
4. **Prediction:** the access-review prediction cites reflect's pattern (reorg removed the admins).
5. **Learning:** resolve one flag with evidence. The score rises, the flag moves to Closed with an explanation, and its prediction drops. Mark another as a false alarm.

Keep a screenshot of each screen as a last-resort fallback.

---

## 11. Backlog (after the MVP exit check passes, in this order)

1. 3-year `ControlTimeline` for one control (hero visual): `GET /controls/{id}/timeline`, Recharts
2. Learning-curve eval script and chart (`/eval/curve`). Report only what was really measured; if improvement is modest, show the concrete behavior change instead.
3. SSE progress streaming
4. More controls and data
5. Auditor question simulator
6. Mobile layout
7. Roadmap only: ISO 27001, real integrations, auth
