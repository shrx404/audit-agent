# RETRACE — Master Build Plan

> **Working name:** RETRACE  
> **Tagline:** **Compliance that remembers.**  
> **Core promise:** A memory-native compliance agent that recognizes recurring control failures by comparing new evidence against an organization’s audit history, then surfaces the previous root cause, remediation, and supporting memory before the same failure becomes another audit finding.

---

## 0. MASTER EXECUTION INSTRUCTION

This file is the single source of truth for the project. Any coding agent working in this repository should read this file before making changes.

### Primary objective
Build a polished, reliable hackathon product in **~11–12 wall-clock hours** that makes Hindsight memory impossible to miss. The product must do **one workflow extremely well**:

1. A compliance/audit finding happened in the past.
2. The organization fixed it.
3. Hindsight retained the finding, root cause, remediation, outcome, and timestamp.
4. A similar problem appears later.
5. RETRACE recalls the relevant history.
6. The agent explains the recurrence using evidence from memory.
7. A human analyst confirms/corrects the result.
8. RETRACE retains the confirmed new experience so the next analysis is better.

### Non-negotiable rule
**Do not turn this into a generic “chat with your policies” app.** The star is **organizational memory + recurrence detection + learning from remediation outcomes**.

### Build philosophy
- Finish the complete P0 flow before adding anything decorative.
- Hindsight must be used for real retain/recall behavior, not as a hidden checkbox integration.
- Every judge-facing conclusion must show **why** it was produced and which prior memory supported it.
- Prefer a strong, believable synthetic company history over fragile third-party integrations.
- No auth, billing, admin console, complex RBAC, multi-tenant SaaS infrastructure, or unnecessary database work during the hackathon.
- No feature may be added if it endangers the core demo.
- Run lint/build/tests after every major milestone.
- Never expose API keys to the browser.
- Never present invented precision as fact. Prefer “Strong recurrence match — 4/5 evidence signals” over fake “92.31% AI confidence.”

---

# 1. WHY THIS PROJECT CAN WIN

The official judging weights are optimized by this design:

| Judging area | Weight | How RETRACE attacks it |
|---|---:|---|
| Innovation | 30% | Detects **recurring compliance failures** and remembers whether previous fixes actually held up; this is more specific than a generic audit chatbot. |
| Hindsight Memory | 25% | Retain → recall → human-confirmed retain is central to the product. Reflect can power cross-history trend analysis. |
| Technical Implementation | 20% | Structured outputs, provenance, deterministic evidence scoring, temporal memories, stable document IDs, evaluation harness, no-memory guardrails. |
| UX | 15% | Judge can literally see the recalled memory, old finding, previous fix, recurrence signals, and control timeline. |
| Real-world Impact | 10% | Repeated audit findings are expensive; organizations repeatedly lose context around why a control failed and whether remediation stayed effective. |

### Judge-facing one-liner
> **“RETRACE remembers every compliance failure, why it happened, and how it was fixed — then catches when the organization starts repeating the same mistake.”**

### What RETRACE is NOT
- Not a policy PDF chatbot.
- Not a generic compliance checklist.
- Not an autonomous legal/compliance decision-maker.
- Not a dashboard with hardcoded alerts.
- Not a vector search demo wearing a fancy UI.

It is a **human-in-the-loop compliance memory agent**.

---

# 2. THE KILLER DEMO STORY

Everything should be built around this exact story first.

## Historical memory: SEC-014
**Date:** 2026-03-14  
**Control:** Privileged Access Management  
**Department:** Finance  
**Finding:** Eight employees who transferred departments retained administrator privileges.  
**Root cause:** The RBAC cleanup worker stopped processing role-change events after a deployment.  
**Remediation:** Restarted the worker, replayed missed role-change events, and added worker-health monitoring.  
**Outcome:** Finding closed and control subsequently passed.  
**Status:** Resolved.

This is seeded into Hindsight before the demo.

## Live finding: SEC-041
Judge/user enters:

> “Four Finance employees transferred teams last month but still retain administrator privileges.”

RETRACE should visibly execute:

1. **Reading current evidence…**
2. **Searching organizational memory…**
3. **Historical finding found: SEC-014**
4. **Comparing recurrence signals…**
5. **Generating evidence-backed investigation plan…**

### Expected result

**STRONG RECURRENCE MATCH — 4/5 signals**

- Same control: Privileged Access ✅
- Same failure type: stale privileges after role transfer ✅
- Same department: Finance ✅
- Same system/dependency: RBAC cleanup workflow ✅ or unknown until investigation
- Same confirmed root cause: unknown ❓

Then:

> **Previously observed root cause:** RBAC cleanup worker failure.  
> **Previous remediation:** worker restart + event replay + health monitoring.  
> **First checks now:** worker health, role-sync queue, recently transferred users, monitoring continuity.

Crucially, RETRACE must say **“possible recurrence”** until current root cause is confirmed.

## Live learning moment
The analyst then confirms:

> “The cleanup worker stopped because its scheduler token expired.”

They enter remediation:

> “Rotated the token and added expiry monitoring.”

Click:

**Confirm & Remember**

RETRACE retains SEC-041 into Hindsight.

Then analyze a second similar finding from Engineering. The agent should now recall **both SEC-014 and SEC-041**, including the newer scheduler-token root cause.

That second recall is the proof that this system is **actually learning during the demo**, not replaying hardcoded seed data.

---

# 3. UNIQUE FEATURES THAT MAKE RETRACE STAND OUT

## P0 — MUST SHIP

### 3.1 Regression Radar
The heart of the product.

Given a new compliance finding, RETRACE searches Hindsight for related historical failures and classifies the result as:

- **Strong recurrence match**
- **Possible recurrence**
- **Related historical context**
- **No meaningful prior match found**

It must never force a recurrence label when evidence is weak.

---

### 3.2 Memory Evidence Drawer
Every analysis includes a visible panel showing exactly what the agent remembered:

- historical finding ID
- date
- control
- department/system
- old finding
- old root cause
- old remediation
- old outcome/status
- source/document ID

This is extremely important: the judge should not need to trust us when we claim Hindsight is being used. They can **see the recalled memories**.

---

### 3.3 Recurrence DNA
Do not expose a mysterious “AI similarity 92%.”

Instead show explainable evidence signals:

| Signal | Example |
|---|---|
| Same control | Privileged Access ↔ Privileged Access |
| Same failure taxonomy | Stale privileges after transfer |
| Same department/system | Finance / IAM |
| Same observed symptom | Admin rights not revoked |
| Same root-cause indicators | RBAC cleanup worker unhealthy |

Display:

> **4 / 5 recurrence signals matched**

This is easy to understand, easy to defend to judges, and technically more credible than fake precision.

---

### 3.4 Human-Confirmed Learning Loop
Never automatically store LLM speculation as permanent memory.

Flow:

`Analyze → Suggest → Human confirms/edits → Retain confirmed case`

Button:

**Confirm & Remember**

This does two things:

1. prevents the memory bank from being poisoned by incorrect AI guesses;
2. creates an obvious live “agent learned something new” demo moment.

This feature should be emphasized heavily during judging.

---

### 3.5 Control Timeline
For a selected compliance control:

```text
JAN          MAR             APR              JUN              SEP
PASS   →     FAIL      →     REMEDIATED  →    PASS      →      FAIL
               │                                             │
            SEC-014                                      SEC-041
               └──────── historical recurrence ─────────────┘
```

The timeline tells the story faster than paragraphs.

---

## P1 — WINNING POLISH AFTER P0 WORKS

### 3.6 Remediation Survival
Show how long a remediation lasted before a similar issue reappeared.

Example:

> **Previous remediation survived 198 days before recurrence.**

This is simple date math but feels extremely enterprise-grade.

Do not imply the remediation “caused” later behavior. It is purely a historical duration between remediation and recurrence.

---

### 3.7 Remediation Drift Detector
If a previous finding was resolved but a similar failure returns, ask:

- Is the old remediation still running?
- Was it bypassed?
- Did a dependency change?
- Did the fix only cover one system/department?

UI copy:

> **Remediation drift suspected**  
> Previous control was marked resolved, but current evidence contradicts expected behavior.

This turns RETRACE from “memory search” into an actual compliance-investigation assistant.

---

### 3.8 Pattern Brief — powered by Hindsight Reflect
On demand, allow the user to ask questions such as:

> “Which controls have repeatedly failed in the last six months?”

> “Which remediation themes appear more than once?”

> “What keeps causing privileged-access regressions?”

Use **Reflect** for cross-history synthesis. Do not use Reflect for every normal analysis because Recall gives better direct provenance and is the faster path.

---

### 3.9 Contradiction / Memory Change Badge
If old memory says a control was successfully remediated but new confirmed evidence shows the issue returned, surface:

> **Historical belief challenged**  
> This control was previously considered resolved; new evidence indicates the control may have regressed.

This aligns beautifully with the idea that organizational knowledge evolves rather than remaining frozen.

---

## P2 — STRETCH ONLY IF EVERYTHING ELSE IS PERFECT

- Visual memory graph: finding → root cause → remediation → outcome → recurrence.
- Policy Drift: connect findings to a small set of seeded policy requirements.
- Executive “Recurring Risk” summary.
- CSV/PDF evidence ingestion.
- One live external integration.
- Multi-company/multi-bank demo.

**Do not build P2 until the demo has survived at least 10 consecutive runs.**

---

# 4. CORE PRODUCT FLOW

```text
AUDITOR / COMPLIANCE ANALYST
          │
          ▼
NEW FINDING / EVIDENCE
          │
          ▼
INPUT VALIDATION + NORMALIZATION
          │
          ▼
HINDSIGHT RECALL
          │
          ├── prior findings
          ├── root causes
          ├── remediations
          ├── outcomes
          └── policy/control context
          │
          ▼
RECURRENCE CANDIDATE SCORER
          │
          ▼
LLM ANALYSIS
          │
          ├── recurrence classification
          ├── explanation
          ├── previous root cause
          ├── previous remediation
          ├── recommended checks
          └── evidence IDs used
          │
          ▼
ANALYSIS UI + MEMORY EVIDENCE
          │
          ▼
HUMAN CONFIRMS / CORRECTS
          │
          ▼
HINDSIGHT RETAIN
          │
          ▼
ORGANIZATIONAL MEMORY GETS BETTER
```

---

# 5. TECH STACK — KEEP IT LEAN

## Frontend / server
- Next.js
- TypeScript
- Tailwind CSS
- Lucide icons
- Framer Motion only for high-value transitions
- Zod for schemas

## Memory
- `@vectorize-io/hindsight-client`
- One Hindsight memory bank for the demo organization

## LLM
Use one fast hosted model through an adapter in `lib/llm.ts`.

The hackathon guide allows any LLM and specifically points teams toward fast Groq-hosted models. Keep provider/model configurable with environment variables so the project is not coupled to one vendor.

## Database
**None for P0.**

- Seed/history JSON exists in the repository for deterministic UI/dashboard rendering.
- Hindsight is the persistent agent memory.
- Newly confirmed cases can be retained in Hindsight.
- Browser-local UI state is acceptable for the live session.

Do not burn time building Postgres/Supabase unless a concrete P1 requirement truly needs it.

---

# 6. HINDSIGHT DESIGN

## 6.1 One bank per organization
For the demo:

```text
bank_id = retrace-acme-compliance
```

All ACME compliance history lives in this bank.

If multi-tenancy is ever added, create separate banks or strict organization scoping rather than mixing unrelated organizations.

---

## 6.2 What we retain
Retain durable organizational memory only:

- confirmed audit findings
- control failures
- affected system / department
- impact / scope
- confirmed root causes
- remediation actions
- remediation outcomes
- control-test outcomes
- policy changes
- approved exceptions
- important dates

Do NOT retain:

- greetings
- transient UI chatter
- speculative LLM guesses
- secrets / credentials
- temporary loading/debug content

---

## 6.3 Stable document IDs
Every compliance case gets a stable document ID:

```text
finding-SEC-014
finding-SEC-041
policy-POL-003
control-test-CTRL-008-2026-08
```

Stable IDs make history easier to reason about and let the same source be updated deliberately instead of duplicated accidentally.

---

## 6.4 Always include timestamps
Historical ordering matters enormously.

Every retained event should use an ISO timestamp.

Example:

```text
2026-03-14T10:00:00Z
```

This enables temporal retrieval and makes the timeline defensible.

---

## 6.5 Metadata
Store useful source metadata for UI provenance:

```json
{
  "findingId": "SEC-014",
  "type": "audit_finding",
  "control": "privileged_access",
  "department": "finance",
  "system": "iam",
  "status": "resolved",
  "source": "seed_audit_history"
}
```

Metadata should help us display where a memory came from. Do not rely on metadata alone for semantic retrieval; meaningful facts must still be present in retained content.

---

## 6.6 Tags
Keep tags simple. Example:

```text
compliance
finding
control:privileged-access
```

Do not over-filter recall so aggressively that useful cross-control history disappears.

---

## 6.7 Retain Mission — advanced differentiator
If bank configuration is available, set a retain mission similar to:

> Focus on compliance-control failures, affected systems and people, root causes, remediation actions, remediation outcomes, policy changes, approved exceptions, recurring patterns, and temporal relationships. Preserve finding IDs and dates. Ignore greetings, meeting logistics, generic filler, and unsupported speculation.

This makes the memory bank itself tuned for compliance work instead of being a generic transcript dump.

---

## 6.8 Recall vs Reflect
### Use Recall for normal finding analysis
Why:
- we need ranked historical evidence;
- we need provenance;
- our own agent will reason over the results;
- latency matters during the demo.

### Use Reflect for cross-history questions
Examples:
- “What failure pattern keeps returning?”
- “Which control has regressed most often?”
- “Which remediations have failed to remain effective?”

Reflect is a P1 feature, not a dependency for core analysis.

---

# 7. MEMORY RECORD FORMAT

Use readable natural-language retained content with clear structure.

```text
Compliance Finding SEC-014
Occurred: 2026-03-14
Control: Privileged Access Management
Department: Finance
System: IAM

Finding:
Eight employees who transferred departments retained administrator privileges.

Impact:
Former role privileges remained active after internal transfers.

Root cause:
The RBAC cleanup worker stopped processing role-change events after a deployment.

Remediation:
The worker was restarted, missed events were replayed, and worker-health monitoring was added.

Outcome:
All stale privileges were removed and the control passed its next validation.

Status:
Resolved.
```

Readable text gives Hindsight enough semantic and causal context while metadata gives the app clean UI fields.

---

# 8. SEED DATA PLAN

Create:

```text
data/seed-findings.json
```

Target **30–40 high-quality historical events**, not hundreds of junk rows.

## Controls represented
1. Privileged Access Management
2. MFA / Authentication
3. Third-Party / Contractor Access
4. Logging & Monitoring
5. Patch / Vulnerability Management
6. Data Retention / Sensitive Data Access

## Dataset composition
- 6 deliberate recurrence chains
- 6 unrelated decoy findings
- 5 remediations that stayed effective
- 3 remediations that later regressed
- 4 approved exceptions
- 4 control-test results
- 3 policy changes
- multiple departments and systems

The dataset should create both obvious and ambiguous cases so the agent does not learn to scream “recurrence” at everything.

## Required recurrence pair #1
SEC-014 → SEC-041 privileged-access transfer failure.

## Required negative example
A new MFA enrollment issue should NOT be falsely matched to stale contractor accounts simply because both involve IAM.

## Required partial-match example
A stale privilege problem in Engineering may be historically related to Finance’s SEC-014, but RETRACE should distinguish:

- same control + same symptom
- different department
- current root cause not yet known

Result should be **Possible recurrence**, not “same incident.”

---

# 9. API CONTRACTS

## POST `/api/analyze`

### Request
```ts
{
  title: string;
  control: string;
  department?: string;
  system?: string;
  description: string;
  evidence?: string;
  occurredAt?: string;
}
```

### Pipeline
1. Validate input with Zod.
2. Build a concise recall query from the actual finding.
3. Call Hindsight Recall.
4. Normalize top relevant memories.
5. Compute explainable recurrence signals for the strongest candidates.
6. Send current finding + memories + signal summary to LLM.
7. Require strict structured output.
8. Verify every cited historical memory exists in recall results.
9. Return analysis.
10. **Do not permanently retain the LLM’s speculative analysis.**

### Response
```ts
{
  classification:
    | "strong_recurrence"
    | "possible_recurrence"
    | "historical_context"
    | "no_match";

  headline: string;
  explanation: string;

  bestHistoricalMatch?: {
    findingId: string;
    date: string;
    control: string;
    finding: string;
    rootCause?: string;
    remediation?: string;
    outcome?: string;
    sourceDocumentId: string;
  };

  recurrenceSignals: {
    name: string;
    matched: boolean | null;
    explanation: string;
  }[];

  recommendedChecks: string[];
  recalledMemories: MemoryEvidence[];
  limitations: string[];
}
```

---

## POST `/api/confirm`

Used only when the human analyst confirms/edits the case.

### Request
```ts
{
  findingId: string;
  occurredAt: string;
  control: string;
  department?: string;
  system?: string;
  finding: string;
  confirmedRootCause?: string;
  remediation?: string;
  outcome?: string;
  status: "open" | "investigating" | "resolved";
  linkedHistoricalFindingIds?: string[];
}
```

### Behavior
- Build canonical memory text.
- Retain to Hindsight with timestamp, stable document ID, metadata, tags.
- Return success + memory/source info.
- UI shows **“Organizational memory updated.”**

---

## GET `/api/pattern-brief` — P1
Uses Hindsight Reflect to create a cross-history summary.

Do not ship this until `/api/analyze` and `/api/confirm` are stable.

---

# 10. RECURRENCE DNA SCORING

Hindsight retrieves the candidate memories. Our own explainability layer compares explicit signals.

Do not claim this score is Hindsight’s internal score.

### Suggested five signals
1. same compliance control
2. same failure taxonomy / symptom
3. same department or affected asset type
4. same system / dependency
5. same confirmed root-cause indicator

### Classification guidance
- **4–5 supported signals:** Strong recurrence candidate
- **2–3 supported signals:** Possible recurrence
- **1 supported signal:** Related context only
- **0 supported signals:** No meaningful recurrence

`null` means “unknown from current evidence,” not false.

The LLM may explain the signals, but code should enforce the valid enum and ensure the result never cites a memory that Recall did not return.

---

# 11. AGENT SYSTEM PROMPT

Use this as the starting point for the analysis agent:

```text
You are RETRACE, an evidence-first compliance investigation assistant.

Your job is to compare a CURRENT FINDING with RELEVANT ORGANIZATIONAL MEMORIES retrieved from Hindsight.

Goals:
1. Determine whether the current finding strongly resembles a prior compliance failure.
2. Separate observed facts from hypotheses.
3. Surface the most relevant historical finding and why it matters.
4. Reuse confirmed prior root causes/remediations only as historical context, never as a guaranteed current cause.
5. Recommend the next checks an analyst should perform.
6. Say explicitly when no useful historical memory exists.

Hard rules:
- Never invent a finding ID, date, root cause, remediation, or outcome.
- Only cite historical memories supplied in this prompt.
- Do not say the current root cause is confirmed unless current evidence confirms it.
- A similar symptom does not prove the same root cause.
- If evidence is weak, classify as possible_recurrence or historical_context.
- If no meaningful memory exists, classify as no_match.
- Do not provide legal advice or claim regulatory certification.
- Keep explanations concise and auditable.

Return only the required structured JSON.
```

---

# 12. UI / UX PLAN

## Visual identity
Professional enterprise/security feel, not a student dashboard.

Suggested direction:
- graphite / near-black base
- off-white text
- amber = caution
- red = confirmed high-risk/recurrence
- green = passed/resolved
- cool cyan/blue = Hindsight memory/retrieval state

Do not use ten gradients or excessive glassmorphism.

## Interaction pacing
Every important action should have visible system state:

```text
Reading evidence…
Searching organizational memory…
3 relevant historical findings recalled…
Comparing recurrence signals…
Preparing investigation plan…
```

Avoid fake long waits. Use short, real state transitions.

---

## Screen 1 — Dashboard

### Top cards
- Active Findings
- Resolved Findings
- Recurring Issues
- Controls Monitored

### Main sections
- Recurring Controls
- Recent Findings
- Remediation Survival
- “Analyze New Finding” primary CTA

### P1
Pattern Brief button.

---

## Screen 2 — Analyze Finding

Inputs:
- title
- control
- department
- system
- date
- description/evidence

Primary CTA:

**Analyze against organizational memory**

During loading, visibly show Hindsight recall progress.

---

## Screen 3 — Analysis Result

Hero block:

```text
STRONG RECURRENCE MATCH
4 / 5 evidence signals
```

Then:
- current finding
- strongest historical match
- previous root cause
- previous remediation
- recommended investigation checks
- limitations / unknowns

Right-side drawer/panel:

**Hindsight Memory Evidence**

Show actual memories recalled.

Bottom:

**Confirm & Remember**

Analyst can edit root cause/remediation before retaining.

---

## Screen 4 — Control Timeline

A horizontal timeline for one control:

- PASS
- FAIL
- REMEDIATED
- PASS
- RECURRENCE

Clicking any finding opens its memory card.

Highlight historical links between repeated failures.

---

# 13. FILE STRUCTURE

```text
retrace/
├─ app/
│  ├─ api/
│  │  ├─ analyze/route.ts
│  │  ├─ confirm/route.ts
│  │  └─ pattern-brief/route.ts        # P1
│  ├─ analyze/page.tsx
│  ├─ controls/[slug]/page.tsx
│  ├─ page.tsx
│  └─ layout.tsx
│
├─ components/
│  ├─ dashboard/
│  ├─ analysis/
│  ├─ memory/
│  ├─ timeline/
│  └─ ui/
│
├─ lib/
│  ├─ hindsight.ts
│  ├─ llm.ts
│  ├─ scoring.ts
│  ├─ schemas.ts
│  ├─ prompts.ts
│  └─ memory-format.ts
│
├─ data/
│  ├─ seed-findings.json
│  ├─ controls.json
│  └─ demo-cases.json
│
├─ scripts/
│  ├─ seed-hindsight.ts
│  └─ eval-recall.ts
│
├─ types/
│  └─ compliance.ts
│
├─ .env.example
├─ README.md
└─ plan.md
```

---

# 14. ENVIRONMENT VARIABLES

```text
HINDSIGHT_BASE_URL=
HINDSIGHT_API_KEY=
HINDSIGHT_BANK_ID=retrace-acme-compliance

LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL=

DEMO_MODE=false
```

Rules:
- API keys server-side only.
- Never prefix secret variables with `NEXT_PUBLIC_`.
- `.env.local` must be gitignored.
- `.env.example` contains names only, no secrets.

---

# 15. INTERNAL EVALUATION HARNESS

This is a quiet technical differentiator and catches bad recall before the demo.

Create `data/demo-cases.json` with ~12 evaluation inputs:

- 4 obvious recurrence cases
- 4 partial/ambiguous matches
- 4 unrelated cases

For each, store:
- expected historical finding ID if applicable
- expected classification range
- must-not-match IDs

`scripts/eval-recall.ts` should:

1. issue the recall query;
2. inspect top recalled memories;
3. report whether expected historical finding appears in top results;
4. optionally run full agent analysis;
5. print a compact pass/fail table.

Target before demo:
- obvious recurrence cases consistently retrieve the correct historical finding;
- unrelated cases do not produce strong recurrence;
- no invented historical IDs.

Do not market this as a formal benchmark. It is an internal reliability test.

---

# 16. TEAM SPLIT

We effectively have ~3.5 serious contributors. Parallelize by dependency.

## Builder A — Product/UI/Integration Lead
Owns:
- Next.js shell
- Dashboard
- Analyze screen
- Analysis result
- Hindsight memory drawer
- Control timeline
- end-to-end integration

Do NOT start with logos, auth, or settings.

---

## Builder B — Hindsight/Memory Lead
Owns:
- `lib/hindsight.ts`
- Hindsight bank configuration
- seed script
- retain/recall tests
- stable document IDs
- timestamps + metadata
- `/api/confirm`

First deliverable must be:

```text
retain one historical finding
→ recall with a related query
→ correct memory comes back
```

Nothing else matters until this works.

---

## Builder C — Agent/LLM + Reliability Lead
Owns:
- `lib/llm.ts`
- Zod response schema
- system prompt
- recurrence-signal logic
- hallucination/provenance guards
- `/api/analyze`
- evaluation harness

Must handle:
- no memory found
- multiple similar memories
- weak match
- malformed LLM output
- LLM timeout/error

---

## Builder D — Beginner / Data + QA
Owns useful, bounded tasks:
- 30–40 realistic seed events
- control list
- demo cases
- manual expected matches
- testing every UI flow
- screenshots
- copy cleanup
- bug log

This is not filler work. Seed quality directly determines how convincing the memory demo is.

---

## Builder E — Half-Time Contributor
Give only isolated tasks that cannot block integration:
- README
- architecture diagram
- timeline visual component
- QA
- demo narration
- article/social/video preparation

Do not make this person the owner of Hindsight or `/api/analyze`.

---

# 17. 12-HOUR EXECUTION CLOCK

## T+00:00 → T+00:30 — LOCK
- Create repo.
- Create Next.js app.
- Add this `plan.md`.
- Set env structure.
- Install Hindsight client + Zod + UI dependencies.
- Decide LLM provider/model.
- Create feature branches only where needed.

**Exit condition:** app boots; env structure exists.

---

## T+00:30 → T+01:30 — MEMORY SPIKE
Builder B:
- create one bank
- retain SEC-014
- recall using a related query
- inspect result

Builder D:
- starts seed dataset

Builder A:
- creates app shell and analyze form

Builder C:
- creates output schema + dummy analysis JSON

**HARD GATE:** Do not proceed to fancy UI if real Hindsight recall is not working.

---

## T+01:30 → T+03:00 — UGLY END-TO-END
- seed at least 10 memories
- `/api/analyze` calls real Recall
- LLM produces schema-valid result
- UI renders it with plain cards

**Exit condition:**

`paste finding → recall memory → return analysis → show source memory`

No animation required yet.

---

## T+03:00 → T+05:00 — CORE PRODUCT
- 30+ seed memories
- robust no-match behavior
- recurrence DNA signals
- memory evidence drawer
- `/api/confirm`
- Confirm & Remember actually retains new case

**Exit condition:** live learning works.

---

## T+05:00 → T+06:00 — FREEZE P0
Run the complete demo five times.

Fix:
- broken states
- slow calls
- schema errors
- duplicate memories
- bad recall query
- misleading language

**At Hour 6 the hackathon project must already be submittable.**

Everything after this is polish/upside.

---

## T+06:00 → T+08:00 — WINNING UX
Build:
- polished result screen
- control timeline
- memory retrieval animation
- responsive layout
- empty/loading/error states
- recurrence DNA visual

Avoid massive animation work.

---

## T+08:00 → T+09:00 — P1 DIFFERENTIATORS
Choose maximum **two**:

1. Remediation Survival
2. Remediation Drift
3. Reflect-powered Pattern Brief

Do not implement all three if it destabilizes P0.

---

## T+09:00 → T+10:00 — RELIABILITY
Run evaluation dataset.

Test:
- obvious recurrence
- partial recurrence
- unrelated finding
- no memory
- conflicting history
- malformed user input
- Hindsight unavailable
- LLM unavailable

Implement graceful fallbacks.

---

## T+10:00 → T+11:00 — DEMO HARDENING
- freeze features
- prepare exact demo seed state
- test network
- test on second laptop/browser
- confirm Hindsight memories exist
- make screenshots
- prepare backup screen recording
- README cleanup

---

## T+11:00 → T+12:00 — STOP CODING
Only critical bugs.

Prepare:
- 60-second judge demo
- 3-minute walkthrough
- architecture explanation
- Hindsight explanation
- “what happens without memory?” answer
- likely judge questions
- repo/submission links

---

# 18. FEATURE KILL ORDER IF WE FALL BEHIND

Cut in this exact order:

1. memory graph
2. policy drift
3. Pattern Brief
4. Remediation Drift
5. fancy charts
6. dashboard statistics
7. multiple control pages

Never cut:
- Hindsight retain
- Hindsight recall
- memory evidence
- recurrence result
- human confirmation
- live retain/learning
- one timeline/demo view

---

# 19. FAILURE / FALLBACK DESIGN

## If Hindsight recall returns nothing
UI:

> **No meaningful historical match found.**  
> Analyze this as a new finding and confirm it to add it to organizational memory.

This is better than hallucinating continuity.

## If LLM fails
Return recalled memories in a fallback card and allow retry.

Never erase the evidence because synthesis failed.

## If Hindsight is temporarily unavailable during judging
Have a clearly labeled `DEMO_MODE` fallback with cached responses only as emergency insurance.

**Do not present cached/demo mode as live Hindsight.** If fallback is active, be transparent.

## If seed ingestion fails
Keep:
- a seed verification command;
- a bank stats/check script;
- an idempotent re-seed path using stable document IDs.

---

# 20. SECURITY + TRUST DESIGN

Because this is a compliance product, credibility matters.

- Server-side API keys only.
- No secrets in Hindsight seed data.
- Human confirms before permanent memory write.
- Historical root cause is context, not proof of current root cause.
- Source IDs/dates visible.
- Agent explicitly states unknowns.
- Avoid legal/certification claims.
- Do not auto-remediate production systems.
- Keep audit trail of what was remembered and why it was used.

Judge answer if asked “What prevents the model from poisoning its own memory?”

> **“We separate inference from durable memory. The model can suggest a recurrence, but only analyst-confirmed facts are retained as new organizational memory.”**

That should be one of our strongest technical answers.

---

# 21. 60-SECOND JUDGE DEMO

## 0–08 sec — Hook
> “Companies don’t just fail compliance controls once. They fix them, lose the context, and repeat the exact failure months later.”

Show SEC-041 new finding.

## 08–20 sec — Analyze
Click **Analyze against organizational memory**.

Visible statuses:
- Searching Hindsight memory
- historical finding recalled
- recurrence signals evaluated

## 20–38 sec — Payoff
Reveal:

> **Strong recurrence match — 4/5 signals**

Show SEC-014:
- same privileged-access problem
- previous root cause
- previous remediation
- date/outcome

Open memory evidence drawer for two seconds.

## 38–48 sec — Investigation value
Show recommended checks:
- RBAC worker health
- role-sync queue
- monitoring continuity

Say:

> “It isn’t guessing the current root cause. It remembers what failed before and tells the analyst where to start.”

## 48–60 sec — Learning
Enter confirmed scheduler-token root cause.
Click **Confirm & Remember**.

Then say:

> “That becomes part of the organization’s memory. The next investigation starts from everything the company has already learned.”

Done.

---

# 22. 3-MINUTE DEMO STRUCTURE

1. **Problem — 20 sec**  
   Repeated findings happen because remediation context disappears across people/time.

2. **Memory architecture — 20 sec**  
   Hindsight retains findings/root causes/remediations/outcomes; Recall retrieves relevant history.

3. **Live recurrence demo — 60 sec**  
   SEC-041 → SEC-014 recall → recurrence DNA → investigation plan.

4. **Evidence/provenance — 25 sec**  
   Open Hindsight Memory Evidence and control timeline.

5. **Live learning — 35 sec**  
   Confirm scheduler-token root cause → retain → second case uses new memory.

6. **Unique layer — 20 sec**  
   Remediation Survival / Drift or Pattern Brief.

---

# 23. QUESTIONS JUDGES WILL PROBABLY ASK

## “Why do you need Hindsight instead of a normal database?”
Answer:

> A database stores records we explicitly query. RETRACE needs semantic, temporal organizational memory: a new finding can be worded differently from an old one, yet still be historically related. Hindsight lets the agent retain facts and relationships from past cases, recall the relevant ones later, and reflect across accumulated history.

## “Is this just RAG?”
Answer:

> Retrieval is part of it, but the product is built as an evolving memory loop. Confirmed outcomes and remediation lessons are retained after each investigation, so later investigations use what the organization actually learned, not only static documents.

## “What if the previous root cause is wrong for the new event?”
Answer:

> We never promote a historical cause to a current fact. It is displayed as prior evidence and a suggested investigation path. The current root cause stays unknown until the analyst confirms it.

## “How do you stop bad AI output becoming memory?”
Answer:

> The agent’s inference is temporary. Durable memory is written only after human confirmation/editing.

## “Why not just search old audit reports?”
Answer:

> Search can find words. RETRACE is built to connect finding → root cause → remediation → outcome across time and surface the relevant organizational lesson when a semantically similar failure returns.

## “What improves over time?”
Answer:

> The memory bank accumulates confirmed findings, root causes, remediations, outcomes, policy changes, and repeat failures. Each new investigation therefore starts with a richer history than the previous one.

---

# 24. README STRUCTURE

Keep README judge-friendly:

1. RETRACE + one-sentence pitch
2. 20-second GIF/screenshot
3. Problem
4. What RETRACE does
5. Why memory changes the workflow
6. Architecture diagram
7. Hindsight integration
8. Core features
9. Setup
10. Demo scenario
11. Safety / human confirmation
12. Team

Do not bury Hindsight under generic frontend details.

---

# 25. SUBMISSION / CONTENT PLAN

The event content guide requires public-facing content in addition to the technical build.

## Article
Per team member, create a technical article centered on a real engineering insight from RETRACE/Hindsight.

Important rule from the guide:
- Do **not** mention the hackathon in the article title or body.
- Make the story about the product/engineering idea.

Possible article angles:
- “Why Our Compliance Agent Refuses to Trust Its Own Memory”
- “I Stopped Storing AI Guesses as Facts”
- “How Hindsight Lets an Audit Agent Recognize Repeated Failures”
- “We Made Compliance Memory Human-Confirmed on Purpose”

## Social post
Again, frame it around the product and memory behavior, not the event.

## Video
Use the exact 3-minute demo structure above.

Capture screenshots during development so nobody has to recreate visuals at the end.

---

# 26. DEFINITION OF DONE

The product is “done enough to submit” only when all of these are true:

### Memory
- [ ] Real Hindsight bank works.
- [ ] Seed script can populate history.
- [ ] Historical timestamps are preserved.
- [ ] Recall returns SEC-014 for the SEC-041 demo scenario.
- [ ] Confirm & Remember retains a new case.
- [ ] A later query can recall the newly confirmed case.

### Agent
- [ ] Structured output validates.
- [ ] No-match path works.
- [ ] Historical causes are clearly labeled as historical.
- [ ] No invented finding IDs.
- [ ] Recommended checks are evidence-based.

### UI
- [ ] Analyze screen works.
- [ ] Result is understandable in <10 seconds.
- [ ] Memory Evidence is visible.
- [ ] Recurrence DNA is visible.
- [ ] Timeline works for at least one control.
- [ ] Loading/error states are present.

### Demo
- [ ] Demo succeeds 10 consecutive times.
- [ ] Backup recording exists.
- [ ] Seed state is verified before judging.
- [ ] Pitch is under 60 seconds.
- [ ] Every teammate knows the one-sentence product definition.

---

# 27. ABSOLUTE DO-NOT-BUILD LIST

Until judging is over, do NOT spend core time on:

- user authentication
- signup/login
- billing
- organization settings
- complex RBAC
- full policy-management suite
- a custom vector DB
- Postgres/pgvector memory
- model fine-tuning
- multi-agent orchestration
- 20 dashboard pages
- real enterprise integrations
- scraping large regulation corpora
- perfect mobile UX
- unnecessary animations

A polished memory-native agent with one unforgettable story beats a giant unfinished compliance platform.

---

# 28. FINAL PRODUCT NORTH STAR

If a teammate asks, “Should we add this feature?”, test it against one question:

> **Does this make the judge more clearly see that RETRACE remembers what the organization learned from previous compliance failures and uses that memory to stop history from repeating?**

If **yes**, consider it.

If **no**, cut it.

The final experience should make the judge think:

> “This is not an AI that read an audit report. This is an AI that remembers the organization’s compliance history.”

That is the product.
