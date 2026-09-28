# BACKEND_PLAN.md — AuditMemory MVP
> Goal: Build the memory/reasoning engine so Hindsight is essential to recurrence detection.
> Success: Recall relevant history, distinguish same-control from same-failure, return source-backed suspected analysis, retain only analyst-confirmed truth, and prove the next analysis changes.
> MVP only. Reliability first.
## 1. Core Flow
```text
New Finding
→ /analyze-finding
→ Hindsight Recall
→ Temporal Resolver
→ LLM Comparison
→ Guardrails
→ Suspected Result
→ /confirm-finding
→ Analyst Confirms/Corrects/Rejects
→ Verified Memory Retained
→ Next Similar Finding Uses It
```

## 2. Responsibilities
- **Hindsight:** findings, root causes, remediations, policy changes, control history, org events, analyst-confirmed outcomes.
- **LLM:** compares the new finding against recalled history and explains recurrence.
- **Guardrails:** same control ID alone is insufficient; claims need memory IDs; current state beats superseded state; no-history means no invented recurrence.
- **Deterministic rules:** overdue test, stale remediation, missing evidence. These never decide recurrence.

## 3. Stack
- FastAPI + Pydantic v2
- Hindsight Cloud + Python SDK
- Groq: `openai/gpt-oss-120b`, fallback `qwen/qwen3-32b`
- JSON seed data
- in-process analysis registry
- pytest
- no DB for MVP

## 4. Structure
```text
backend/app/
├── main.py
├── config.py
├── schemas.py
├── memory/
│   ├── client.py
│   ├── seed.py
│   ├── formatter.py
│   ├── recall.py
│   └── temporal.py
├── agent/
│   ├── llm.py
│   ├── analyzer.py
│   ├── checks.py
│   ├── registry.py
│   └── prompts.py
└── routes/
    ├── analyze.py
    └── confirm.py
scripts/
├── hello_hindsight.py
├── validate_data.py
├── seed_memory.py
├── smoke_test.py
├── learning_check.py
└── reset_demo.py
```

## 5. Environment
```env
HINDSIGHT_BASE_URL=
HINDSIGHT_API_KEY=
HINDSIGHT_BANK_ID=
GROQ_API_KEY=
AUDIT_TODAY=2026-09-28
```
Never commit secrets.

## 6. Hindsight Go/No-Go
Before app work:
1. retain 2 memories
2. recall them
3. call reflect once
4. measure retain→recall delay
5. inspect recall result fields
6. verify mapping to our memory IDs
7. verify fresh-bank/reset behavior
8. document actual SDK behavior in `docs/hindsight-notes.md`

If this fails, stop and fix it first. Never let agents guess SDK signatures.

## 7. Memory Model
Bank: `finpay-audit`

Every durable memory must be verified, dated, self-contained, and linked to a subject.

Example:
```text
[MEM M-004 | type=finding | trust=verified | subject=F-2024-03 | as_of=2024-03-12 | supersedes=none]
On 2024-03-12, finding F-2024-03 against CC6.2 recorded that quarterly production admin access reviews were not performed.
```

Required metadata: `mem_id`, `type`, `trust`, `subject`, `as_of`, `supersedes`, `text`.

Memory types:
- finding
- root_cause
- remediation
- policy_change
- control_test
- org_event
- analyst_confirmation

One fact cluster per retain call.

## 8. Trust Model
**Verified, may be stored:** seeded history; analyst-confirmed finding/root cause/remediation/rejection.
**Suspected, never durable:** AI recurrence guess; guessed root cause; guessed remediation.

Hard rule:
```text
/analyze-finding NEVER retains
/confirm-finding is the only live retain path
```

## 9. Temporal Truth
1. every memory has `as_of`
2. same subject may have multiple states
3. explicit `supersedes` wins
4. otherwise newest verified `as_of` = current
5. older states remain history
6. current state is authoritative
7. analyst-confirmed superseding state outranks older state

Tests: policy v3 > v2; reopened remediation > older done state.

## 10. Seed Data
Target: **26 memories** supporting:
- repeated access-review failures
- root causes
- ineffective + reopened remediation
- one resolved decoy
- policy change
- ownership/reorg event
- staff departure
- overdue test
- stale ticket
- scenarios R1, R2, R1b, D1

## 11. Recall Strategy
Run 3 queries:
1. finding text
2. department + failure description
3. root-cause/remediation context

Then merge, dedupe, cap ~15, parse headers, run temporal resolver.
Recall is the MVP-critical Hindsight operation.

## 12. Recurrence Comparison
For each candidate rate:
1. semantic similarity
2. failure type
3. root cause
4. organizational context
5. previous remediation

Each returns `match | partial | none | unknown`, one-line reason, and supporting memory IDs.

## 13. Recurrence Guardrail
Same `control_id` alone never means recurrence.
```python
possible_recurrence = (
    failure_type == "match"
    and semantic_similarity in {"match", "partial"}
    and (
        root_cause in {"match", "partial"}
        or remediation in {"ineffective", "unverified"}
    )
)
```
R2 must prove this works. Drop unsupported claims.

Confidence:
- high = failure type + root cause + remediation/history align
- medium = two strong dimensions align
- low = weak/incomplete evidence
No percentages.

## 14. Deterministic Checks
- `overdue_test`: `AUDIT_TODAY - last_tested > required_frequency_days`
- `stale_ticket`: open > 180 days OR owner inactive
- `missing_evidence`: new finding lacks evidence OR related done remediation lacks evidence

These never set recurrence.

## 15. LLM Rules
Prompt must say:
- use only supplied memories
- never invent history
- same control ID alone is not evidence
- answer `unknown` when memory is silent
- current state beats history
- every claim cites memory IDs
- suspected is not verified
- analyst-confirmed state has highest trust
- strict JSON only

Malformed output: strip fences → retry once → fallback model → clean error.

## 16. Reflect
Reflect is advisory only:
- max ~10 sec
- not citable
- continue without it
If behind schedule: **cut reflect first**.

## 17. Core Schemas
```python
class NewFindingRequest(BaseModel):
    control_id: str
    department: str
    finding: str
    evidence_ref: str | None = None

class AnalyzeFindingResponse(BaseModel):
    analysis_id: str
    status: Literal["suspected"]
    possible_recurrence: bool
    recurrence_confidence: Literal["low","medium","high"] | None
    related_past_findings: list[RelatedFinding]
    previous_root_cause: PreviousRootCause | None
    previous_remediation: PreviousRemediation | None
    explanation: str
    memories_used: list[RecalledMemory]
    deterministic_checks: list[Flag]
    warnings: list[str]

class ConfirmFindingRequest(BaseModel):
    analysis_id: str
    decision: Literal["confirm_recurrence","not_recurrence","correct"]
    linked_finding_ids: list[str] = []
    confirmed_root_cause: str | None = None
    confirmed_remediation: str | None = None
    outcome: Literal["open","remediated_with_evidence","remediated_no_evidence","accepted_risk"] = "open"
    analyst: str
    note: str | None = None
```

## 18. API
### GET `/health`
```json
{"ok":true,"hindsight":true,"llm":true}
```

### POST `/analyze-finding`
1. validate
2. recall
3. dedupe
4. temporal resolve
5. deterministic checks
6. optional reflect
7. LLM judge
8. guardrails
9. save suspected analysis in registry
10. return source-backed result

Never retain.

### POST `/confirm-finding`
1. load suspected analysis
2. validate analyst decision
3. construct verified confirmation memory
4. retain to Hindsight
5. verify/poll retrievability
6. return retained memory IDs

Only live write endpoint.

## 19. Analysis Registry
In-memory only. Store:
- analysis ID
- original request
- recalled IDs
- suspected result
- AI suggestion

No DB needed.

## 20. Required Scenarios
### R1 — True recurrence
Access review not performed.
Expected: recurrence true, old findings, ownership-gap root cause, ineffective remediation, sources.

### R2 — Same control, different failure
Contractor granted admin without approval.
Expected: recurrence false; same-control history may be related only.

### R1b — Learning proof
Run before and after R1 confirmation.
Expected after: new verified memory recalled, root cause changes, remediation guidance changes.

### D1 — Rule-only
Backup restore test missing.
Expected: deterministic checks, no recurrence without matching history.

## 21. Build Order
### B0 — Hindsight (0:00–1:00)
- [ ] verify SDK
- [ ] retain / recall / reflect
- [ ] document behavior
**Exit:** round trip works.

### B1 — Seed + Wrapper (1:00–3:00)
- [ ] validate data
- [ ] formatter + client wrapper
- [ ] seed script + smoke tests
- [ ] reset/idempotency
**Exit:** expected memories recall correctly.

### B2 — Recall + Temporal + Checks (3:00–4:15)
- [ ] FastAPI + health
- [ ] recall builder
- [ ] temporal resolver
- [ ] deterministic checks
- [ ] analyze v0
**Exit:** R1 returns correct history before LLM.

### B3 — Analyzer (4:15–6:15)
- [ ] Groq + fallback
- [ ] strict JSON + prompts
- [ ] optional reflect
- [ ] analyzer + guardrails
- [ ] scenario tests
**Exit:** R1 true, R2 false, D1 rule-only.

### B4 — Confirm + Learn (6:15–7:45)
- [ ] confirm endpoint
- [ ] trust tests
- [ ] retain verified confirmation
- [ ] retrievability check
- [ ] learning check + reset script
**Exit:** R1b changes after confirmation.

### B5 — Hardening (7:45–9:30)
- [ ] frontend integration
- [ ] degraded states
- [ ] malformed model handling
- [ ] validation
- [ ] full browser flow

## 22. Tests
**Unit:** temporal resolver, overdue, stale ticket, missing evidence, recurrence guardrail, unsupported citation removal.

**Trust:** analyze never retains; suspected content never retained; confirm is only live retain path.

**Scenario:** R1 true; R2 false; D1 rule-only; R1b changes.

**Degraded:** empty recall; Hindsight unavailable; invalid model JSON; invalid control ID.

## 23. Learning Check
`scripts/learning_check.py` must prove:
1. empty bank + R1 → no history, no recurrence
2. seeded bank + R1 → recurrence with evidence
3. confirm corrected R1 → verified memory retained
4. R1b → confirmed memory appears and output changes
5. optional R2 rejection test

## 24. Error Handling
- Hindsight unavailable → `hindsight_degraded`, never invent history
- empty recall → `no_history`
- malformed LLM → retry → fallback → clean error
- invalid memory citation → drop unsupported claim
- unknown control → validation error
- indexing delay → poll briefly, else `retrievable:false`

## 25. Backend Definition of Done
- [ ] Hindsight hello-world passes
- [ ] 26 memories seeded + smoke tests pass
- [ ] `/analyze-finding` works
- [ ] R1 true; R2 false
- [ ] same control alone never decides recurrence
- [ ] root cause/remediation source-backed
- [ ] deterministic checks separate
- [ ] all AI analysis is suspected
- [ ] analyze never retains
- [ ] confirm is only live retain path
- [ ] correction becomes verified, recallable memory
- [ ] R1b changes after confirmation
- [ ] temporal current/history works
- [ ] no-history never hallucinates
- [ ] degraded states safe
- [ ] frontend completes real flow

## 26. Do Not Build in MVP
Do not build: readiness score, prediction engine, free-text Q&A, auth, DB, uploads/PDF parsing, live integrations, multiple frameworks, SSE, timeline API, analytics dashboard.

If behind:
1. cut reflect
2. cut optional rejection-learning
3. never cut R2 guardrail
4. never cut confirmation/retain loop

## 27. Backend Success Statement
> Hindsight retrieves the exact historical failures, root causes, and remediations needed to judge a new finding; the system distinguishes the same control from the same failure; AI conclusions remain suspected until a human verifies them; and verified knowledge becomes durable memory that changes the next analysis.
