# PLAN.md - AuditMemory: A Compliance and Audit Agent With Memory

> Hackathon: AI Agents That Learn Using Hindsight
> Problem statement: Compliance and Audit Agent
> Pitch line: **"Auditors remember everything you got wrong last year. Your team doesn't. We fix that."**

---

## 0. How To Use This File

- This file is the single source of truth. Put it in the repo root next to `AGENTS.md`.
- Every task has an ID like `T2.3`. Tick the box when done. Commit after each ticked box.
- Sections marked **[VERIFY]** contain things agents commonly get wrong. Check them by hand.
- Anything marked **[STRETCH]** is cut first if time runs short.
- Do not start Phase 4 (frontend polish) until the Phase 2 exit check passes. A pretty UI on a broken memory loop scores badly.

---

## 1. Hackathon Rules Recap (from the official doc)

### 1.1 Hard requirements

- [ ] All teams MUST build using **Hindsight**
- [ ] Project must clearly demonstrate how Hindsight memory is used
- [ ] Submit: **GitHub repo** (clean, documented code)
- [ ] Submit: **Demo video** showing the agent in action
- [ ] Submit: **Live demo** to judges
- [ ] Submit: **Explanation of how Hindsight memory is used** (goes in README)
- [ ] EVERY team member completes: **Article + Social Media post + Video** from the official content guide
- [ ] Share the project based on the official content guide challenges

### 1.2 Judging weights and what we do about each

| Criteria                 | Weight | What judges look for                   | Our answer                                                                         |
| ------------------------ | ------ | -------------------------------------- | ---------------------------------------------------------------------------------- |
| Innovation               | 30%    | Fresh take, beyond chatbot territory   | Predict next findings, not just recall old ones. Catch "fixed with no evidence"    |
| Use of Hindsight Memory  | 25%    | Memory central, agent visibly improves | Memory on/off toggle, memory panel with citations, feedback loop, reflect insights |
| Technical Implementation | 20%    | Clean, architected, handles edge cases | Retry and fallback layer for LLM function-calling errors, typed schemas, tests     |
| User Experience          | 15%    | Intuitive, compelling demo flow        | Readiness score, 3-year timeline, one-click demo scenario                          |
| Real-world Impact        | 10%    | Genuine problem, path to adoption      | SOC 2 prep pain, prep time drops from weeks to days                                |

### 1.3 Doc guidance we must follow

- **Avoid student-centric projects.** Compliance is a professional workflow. Good.
- **Keep scope tight:** one workflow, one persona, one value proposition.
- **Realistic data is the number one thing** that makes it look real. Budget real time for it.
- **Show the learning curve:** interaction 1 generic, interaction 5 personalized, interaction 20 feels like it knows you.
- **Handle function calling errors** with the recommended Groq models.
- **Think like a demo:** value obvious in 60 seconds.

---

## 2. Product Definition

### 2.1 One-liner

An agent that remembers a company's full audit history (findings, fixes, evidence, control tests) and uses it to predict what the next auditor will find, before they arrive.

### 2.2 Persona and scenario (fixed, do not change)

- **Company:** FinPay (fictional fintech, 120 employees, payments API)
- **Persona:** Arjun Mehta, Compliance Manager
- **Situation:** SOC 2 Type II audit begins in 30 days
- **Frameworks in scope:** SOC 2 Trust Services Criteria (Security focus)
- **History available:** 3 years of audit cycles (2023, 2024, 2025) plus current-year test logs

### 2.3 The four core capabilities

1. **Recall:** "What did auditors say about access reviews, and is it fixed?"
2. **Detect:** flag repeat findings, overdue control tests, stale remediation tickets, and fixes marked done with no evidence
3. **Predict:** output the likely findings for the coming audit with confidence and reasoning (uses Hindsight reflect)
4. **Learn:** user marks items resolved or false alarm, and future answers change accordingly

### 2.4 Explicit non-goals (say no to these)

- No real integrations with AWS, Okta, Jira, or any live system
- No support for frameworks beyond SOC 2 (mention ISO 27001 as roadmap only)
- No user accounts or authentication
- No document upload or PDF parsing
- No model training or fine-tuning of any kind

---

## 3. Architecture

### 3.1 Diagram

```
                +--------------------------------+
                |        Next.js Frontend        |
                |  Readiness | Timeline | Memory |
                +---------------+----------------+
                                | REST + SSE
                +---------------v----------------+
                |        FastAPI Backend         |
                |  routes / agent / schemas      |
                +---+---------------+-----------+
                    |               |
        +-----------v--+     +------v---------+
        |  Hindsight   |     |   Groq LLM     |
        |  retain      |     |  gpt-oss-120b  |
        |  recall      |     |  qwen3-32b     |
        |  reflect     |     |  (fallback)    |
        +--------------+     +----------------+
```

### 3.2 Tech stack

| Layer     | Choice                                                 | Why                                 |
| --------- | ------------------------------------------------------ | ----------------------------------- |
| Frontend  | Next.js, TypeScript, Tailwind                          | Your existing stack                 |
| Charts    | Recharts                                               | Fast timeline and score visuals     |
| Backend   | FastAPI, Pydantic v2                                   | Typed schemas, your existing stack  |
| Memory    | Hindsight Cloud (`hindsight-client` Python SDK)        | Required by rules                   |
| LLM       | Groq: `openai/gpt-oss-120b`, fallback `qwen/qwen3-32b` | Recommended by doc, fast, free tier |
| Data      | JSON seed files                                        | No database needed                  |
| Streaming | Server-Sent Events                                     | Simpler than WebSockets             |

### 3.3 Hindsight API surface we use **[VERIFY]**

From the official docs (confirm against the live docs before coding):

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="https://<your-cloud-url>", api_key="<key>", timeout=30.0)

# Retain (store)
client.retain(bank_id="finpay-audit", content="...", context="audit finding", timestamp="2024-06-15T10:00:00Z")

# Recall (search)
results = client.recall(bank_id="finpay-audit", query="access review findings")
for r in results.results:
    print(r.text)

# Reflect (synthesize insights)
answer = client.reflect(bank_id="finpay-audit", query="What findings will recur?")
print(answer.text)
```

Notes:

- Recall runs 4 strategies in parallel (semantic, keyword, graph, temporal), so include **dates** and **control IDs** in retained text. That makes temporal and keyword recall work well.
- Reflect forms new connections between memories, which is our "predict repeats" engine.
- Check whether the Cloud SDK constructor needs `api_key`. The quickstart shows a local URL. **Do not let an agent guess this.**
- The client may need `nest_asyncio` inside notebooks. Not needed in FastAPI, but relevant for scratch testing.

### 3.4 Memory design (this is 25% of the score, think hard here)

**One bank:** `finpay-audit`

**What we retain, as separate memories.** Each is a short, self-contained natural-language paragraph, because Hindsight extracts entities and facts from text:

| Memory type        | Example content                                                                                                                                                       | Context tag     |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| Audit finding      | "On 2024-03-12, the SOC 2 auditor raised finding F-2024-03 against control CC6.2 (access reviews): quarterly user access reviews were not performed. Severity: High." | `audit finding` |
| Remediation ticket | "Ticket REM-118 opened 2024-03-20, owner Priya Nair, to fix F-2024-03 by implementing quarterly access reviews. Marked done on 2024-06-01. Evidence attached: none."  | `remediation`   |
| Control test log   | "Control CC7.2 (backup restore test) was last tested on 2024-01-15 by Rahul Iyer. Result: passed. Policy requires testing every 12 months."                           | `control test`  |
| Policy change      | "On 2024-09-01 the access management policy v3 was published, moving reviews from quarterly to monthly."                                                              | `policy change` |
| User feedback      | "On 2026-09-28 Arjun marked F-2025-02 as resolved with evidence link EV-902."                                                                                         | `user feedback` |
| Org events         | "In 2024-02 the platform team was reorganized and three admins left."                                                                                                 | `org event`     |

**Rules for writing memories:**

- Always include: date, control ID, finding or ticket ID, owner, status
- One fact cluster per retain call (do not dump a whole spreadsheet in one call)
- Use consistent ID formats so keyword recall works: `F-YYYY-NN`, `REM-NNN`, `CC6.2`
- Set `timestamp` on every retain so temporal recall works

**How each Hindsight operation is used (this goes in the README explanation):**

- **Retain:** loads 3 years of findings, tickets, tests, policy changes, and every user feedback event
- **Recall:** pulls relevant history for a control, a question, or a predicted finding
- **Reflect:** detects cross-year patterns (for example "access findings follow reorgs") and generates the prediction narrative

### 3.5 Data schemas (Pydantic and TypeScript must match)

```python
class Finding(BaseModel):
    id: str                 # F-2024-03
    control_id: str         # CC6.2
    control_name: str
    severity: Literal["low", "medium", "high"]
    raised_date: date
    auditor_note: str
    audit_cycle: int        # 2024

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

class Flag(BaseModel):
    kind: Literal["repeat_finding", "overdue_test", "stale_ticket", "done_no_evidence"]
    control_id: str
    severity: Literal["low", "medium", "high"]
    explanation: str
    sources: list[str]      # memory or record IDs that justify it

class Prediction(BaseModel):
    control_id: str
    likelihood: Literal["low", "medium", "high"]
    reasoning: str
    sources: list[str]

class ReadinessReport(BaseModel):
    score: int              # 0-100
    flags: list[Flag]
    predictions: list[Prediction]
    priority_actions: list[str]
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
│   ├── hindsight-notes.md        # pasted real API notes
│   ├── demo-script.md
│   └── architecture.png
├── data/
│   ├── controls.json             # ~25 SOC 2 controls from Vanta control set
│   ├── findings.json
│   ├── remediations.json
│   ├── control_tests.json
│   ├── policy_changes.json
│   └── org_events.json
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── schemas.py
│   │   ├── memory/
│   │   │   ├── client.py         # Hindsight wrapper
│   │   │   ├── seed.py           # load JSON -> retain
│   │   │   └── formatter.py      # record -> memory text
│   │   ├── agent/
│   │   │   ├── llm.py            # Groq client + retry + fallback
│   │   │   ├── detect.py         # rule-based flag detection
│   │   │   ├── predict.py        # reflect + LLM prediction
│   │   │   ├── readiness.py      # score calculation
│   │   │   └── prompts.py
│   │   └── routes/
│   │       ├── readiness.py
│   │       ├── ask.py
│   │       ├── feedback.py
│   │       ├── memory.py
│   │       └── demo.py
│   └── tests/
├── scripts/
│   ├── generate_data.py          # LLM synthetic data generator
│   ├── seed_memory.py
│   ├── smoke_test.py
│   └── eval_learning_curve.py
└── frontend/
    ├── package.json
    └── src/
        ├── app/
        ├── components/
        │   ├── ReadinessGauge.tsx
        │   ├── FlagList.tsx
        │   ├── ControlTimeline.tsx
        │   ├── MemoryPanel.tsx
        │   ├── MemoryToggle.tsx
        │   ├── AskBox.tsx
        │   └── FeedbackButtons.tsx
        └── lib/api.ts
```

---

## 5. The Data Plan (highest leverage, do it well)

### 5.1 Sources

- **Control backbone:** Vanta Control Set on GitHub (`VantaInc/vanta-control-set`), SOC 2 JSON. Pick about 25 controls focused on access, change management, backups, vendor risk, logging, and incident response.
- **Optional cross-check:** NIST OSCAL catalogs or the Secure Controls Framework for ID and naming ideas.
- **Kaggle audit datasets:** optional flavor only. None model findings plus remediation over time, so do not depend on them.
- **Licensing:** the official SOC 2 criteria text is AICPA copyright. Use control names and IDs from open sets and **write your own descriptions**.

### 5.2 What to generate synthetically

| File                  | Count    | Notes                                |
| --------------------- | -------- | ------------------------------------ |
| `findings.json`       | 18 to 25 | Across 2023, 2024, 2025 audit cycles |
| `remediations.json`   | 15 to 22 | Linked to findings by ID             |
| `control_tests.json`  | ~25      | One per selected control             |
| `policy_changes.json` | 6 to 10  | Some explain why findings recur      |
| `org_events.json`     | 4 to 6   | Reorgs, departures, tool migrations  |

### 5.3 The four traps (these ARE the demo, seed them deliberately)

| Trap                           | How to seed it                                                                   | What the agent should say                                          |
| ------------------------------ | -------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| **T-A: Repeat finding**        | Access review finding (CC6.2) in 2023 AND 2024, "fixed" in between               | "This exact finding recurred. The 2024 fix had no follow-through." |
| **T-B: Overdue control test**  | Backup restore test (CC7.2 or similar) last tested 14 months ago, policy says 12 | "Overdue by 2 months. Auditor will flag this."                     |
| **T-C: Stale ticket**          | Vendor risk remediation open 9 months, owner has left the company                | "Open 9 months, owner no longer at FinPay, unowned."               |
| **T-D: Done with no evidence** | Remediation marked done, `evidence_ref = null`                                   | "Marked done but no evidence exists. Auditor will not accept it."  |

Add one **decoy** so the agent must show discipline: a finding that looks scary but is genuinely resolved with evidence. The agent must NOT flag it. This proves precision and earns technical points.

### 5.4 Realism checklist

- [ ] Real-sounding Indian and international employee names, consistent across files
- [ ] Real SOC 2 control IDs (CC6.1, CC6.2, CC7.2, CC8.1, and so on)
- [ ] Believable auditor language ("Management did not provide evidence that...")
- [ ] Dates that make sense (tickets open after findings, not before)
- [ ] Reorg and departure events that plausibly explain the recurring findings
- [ ] Mixed severities, not everything "high"

### 5.5 Generation approach

1. Write the trap list and control list by hand first
2. Prompt the LLM to generate the files, giving it the traps as hard requirements
3. Validate with a script: every `finding_id` in remediations exists, dates are ordered, all four traps present, decoy present
4. Manually read the whole dataset once. Fix anything that sounds fake.

---

## 6. Phased Build Plan

Assume roughly **24 to 36 hours total**. Scale the hour ranges down proportionally if your window is shorter. Order matters more than the exact hours.

### PHASE 0: Setup and Alignment (Hours 0 to 2)

**Everyone together. No coding before this is done.**

- [ ] **T0.1** Register on Hindsight Cloud, create an account
- [ ] **T0.2** Apply promo code **MEMHACK99** in the billing section AFTER registering ($50 credits)
- [ ] **T0.3** Create Groq account and API key, test one call with `openai/gpt-oss-120b`
- [ ] **T0.4** Join the Hindsight community Slack (for fast answers)
- [ ] **T0.5** Create GitHub repo, add folders from Section 4, add `.gitignore` (must include `.env`)
- [ ] **T0.6** Create `.env.example` with `HINDSIGHT_BASE_URL`, `HINDSIGHT_API_KEY`, `GROQ_API_KEY`, `HINDSIGHT_BANK_ID`
- [ ] **T0.7** Read the Hindsight docs quickstart and Python client page. Paste the real API notes into `docs/hindsight-notes.md`
- [ ] **T0.8** Run the Hindsight hello-world (retain, recall, reflect) from a plain Python script. **This is the go/no-go check.**
- [ ] **T0.9** Freeze the schemas in Section 3.5 and the API contract in Section 7
- [ ] **T0.10** Write `AGENTS.md` and `SPEC.md` (see Section 12), commit
- [ ] **T0.11** Install Antigravity IDE, open the repo as a workspace

**Exit check:** hello-world retain, recall, reflect all return results. If not, ask in the Slack before doing anything else.

---

### PHASE 1: Data and Memory Loop (Hours 2 to 8)

- [ ] **T1.1** Pull the Vanta SOC 2 control JSON, select about 25 controls, save to `data/controls.json`
- [ ] **T1.2** Write the traps list and decoy by hand (Section 5.3)
- [ ] **T1.3** Write `scripts/generate_data.py` and produce all data files
- [ ] **T1.4** Write a data validation script (references valid, dates ordered, four traps plus decoy present)
- [ ] **T1.5** Manually read the data. Fix fake-sounding parts.
- [ ] **T1.6** Write `memory/formatter.py`: turn each record into a rich memory paragraph (Section 3.4 rules)
- [ ] **T1.7** Write `memory/client.py`: thin wrapper around Hindsight with retry on transient errors
- [ ] **T1.8** Write `memory/seed.py` and `scripts/seed_memory.py`: retain every record with correct timestamps
- [ ] **T1.9** Verify in the Hindsight UI that documents and entities appear for the bank
- [ ] **T1.10** Write `scripts/smoke_test.py`:
  - recall "access review findings" returns both the 2023 and 2024 findings
  - recall "backup restore test" returns the overdue test
  - recall "vendor risk ticket" returns the stale ticket
  - reflect "What findings tend to recur and why?" mentions access reviews
- [ ] **T1.11** Make seeding **idempotent** (running twice must not create duplicates). Use a stable document ID per record if the API supports it **[VERIFY]**, otherwise a fresh bank per seed run.

**Exit check (Phase 1):** the smoke test passes. Recall returns the right records for each trap. Reflect produces a sensible cross-year insight. **If reflect output is weak, improve the memory text quality, not the code.**

---

### PHASE 2: Agent Brain (Hours 8 to 16)

- [ ] **T2.1** `agent/llm.py`: Groq client with:
  - primary `openai/gpt-oss-120b`, fallback `qwen/qwen3-32b`
  - retry with exponential backoff (3 attempts)
  - JSON parse failure handling: strip code fences, re-ask once with "return valid JSON only"
  - function calling error handling (the doc warns about this explicitly)
  - request timeout, and a clear error object returned, not a crash
- [ ] **T2.2** `agent/detect.py`: deterministic flag detection from structured records (do NOT rely only on the LLM):
  - repeat finding: same `control_id` in 2 or more audit cycles
  - overdue test: `today - last_tested > required_frequency_days`
  - stale ticket: open longer than 180 days, or owner not in current staff list
  - done with no evidence: `status == done` and `evidence_ref is None`
  - decoy is NOT flagged (resolved with evidence)
- [ ] **T2.3** `agent/predict.py`:
  - for each flagged control, `recall` related history
  - call Hindsight `reflect` for cross-year patterns
  - LLM combines recalled memories plus reflect output into `Prediction` objects with reasoning
  - every prediction must include `sources` (record or memory IDs)
- [ ] **T2.4** `agent/readiness.py`: score from 0 to 100
  - start at 100, subtract weighted penalties by flag severity and kind
  - repeat findings and done-no-evidence weigh heaviest
  - keep the formula simple and explainable, show it in the UI tooltip
- [ ] **T2.5** `agent/prompts.py`: system prompts that force citations ("every claim must reference a source ID; if no source, say you do not know")
- [ ] **T2.6** **Feedback loop:** `POST /feedback` accepts `{flag_id, action: resolved | false_alarm | still_open, evidence_ref?, note?}`
  - retain the outcome to Hindsight as a dated memory
  - update in-process state so the next readiness run reflects it
  - next `/readiness` must both change the score AND explain why ("closed on 2026-09-28 with evidence EV-902")
- [ ] **T2.7** **Memory on/off mode:** a request flag `use_memory` (default true). When false, the agent answers with the LLM only, no recall, no reflect. This powers the before/after demo.
- [ ] **T2.8** Unit tests for `detect.py` (each trap, the decoy, edge cases)
- [ ] **T2.9** Edge case handling:
  - empty recall result: say "no history found", never invent
  - Hindsight unreachable: degrade gracefully with a clear message
  - LLM returns malformed JSON: retry then fallback model
  - unknown control ID in a question: polite response

**Exit check (Phase 2):** from a script or curl, with memory ON the agent returns all four traps with correct sources and does not flag the decoy. With memory OFF it returns generic advice. After a feedback call, the score changes and the explanation cites the feedback. **Do not start the frontend polish until this passes.**

---

### PHASE 3: API Layer (Hours 12 to 18, can overlap with Phase 2 after contract freeze)

- [ ] **T3.1** FastAPI app, CORS for the frontend origin, env config loader
- [ ] **T3.2** Implement endpoints per Section 7 contract
- [ ] **T3.3** SSE endpoint that streams agent progress steps so the UI shows "Recalling history...", "Detecting gaps...", "Predicting findings..."
- [ ] **T3.4** `GET /memory/trace` returns exactly which memories were used for the last answer (powers the memory panel)
- [ ] **T3.5** `POST /demo/reset` restores the seeded state so the demo is repeatable
- [ ] **T3.6** Global exception handler returning structured errors
- [ ] **T3.7** Basic integration tests hitting each route

**Exit check:** every route works via curl with correct JSON shapes. `/demo/reset` returns to a known state in under 10 seconds.

---

### PHASE 4: Frontend (Hours 14 to 24, parallel with Phase 3)

- [ ] **T4.1** Scaffold Next.js plus Tailwind, create `lib/api.ts` typed client from the contract
- [ ] **T4.2** Layout: header with company and audit countdown, left readiness panel, center flags and answers, right memory panel
- [ ] **T4.3** `ReadinessGauge`: animated 0 to 100 score with color bands
- [ ] **T4.4** `FlagList`: cards per flag with kind badge, severity, explanation, and clickable source chips
- [ ] **T4.5** `MemoryPanel`: shows the recalled memories behind the current answer, with dates and match relevance. **This is the hero of the memory score.**
- [ ] **T4.6** `MemoryToggle`: big, obvious ON/OFF switch. When OFF, memory panel shows empty and answers turn generic.
- [ ] **T4.7** `ControlTimeline`: 3-year horizontal timeline for one control (finding, fix, retest, regression) using Recharts. **This is the hero visual, spend real design time here.**
- [ ] **T4.8** `AskBox`: free-text question with 3 suggested prompts, streaming response
- [ ] **T4.9** `FeedbackButtons` on each flag: Resolved (with evidence field), False alarm, Still open. Score animates on change.
- [ ] **T4.10** Predictions section: "Likely findings next audit" with likelihood chips and reasoning
- [ ] **T4.11** Loading, empty, and error states everywhere (UX and edge case points)
- [ ] **T4.12** Mobile-safe layout as a bonus, desktop must look excellent for the live demo
- [ ] **T4.13** Dark or light polish pass, consistent spacing, one accent color, readable font sizes for a projector

**Exit check:** the full demo flow works end to end in the browser without touching the terminal.

---

### PHASE 5: Learning Curve Evidence (Hours 22 to 28)

The doc says: "Interaction 1: generic. Interaction 5: personalized. Interaction 20: feels like it knows you."

- [ ] **T5.1** `scripts/eval_learning_curve.py`: run a scripted series of feedback interactions and record after each:
  - false alarm rate (flags the user rejects)
  - accuracy of flags against ground truth (we know the seeded traps)
  - readiness score movement
- [ ] **T5.2** Design 8 to 12 scripted interactions that visibly change behavior (for example rejecting a flag type then confirming the agent stops raising similar false alarms)
- [ ] **T5.3** Chart the result (before memory vs after memory, accuracy across interactions) and embed it in the UI and README
- [ ] **T5.4** **Be honest in the numbers.** Report what the eval actually measured. Do not fabricate a curve. If improvement is modest, say so and show the concrete behavior change instead.
- [ ] **T5.5** **[STRETCH]** Auditor question simulator: agent asks "show evidence of Q2 access review" and shows whether the records can answer

**Exit check:** you have one real, reproducible chart or table showing improvement, and you can explain how it was measured.

---

### PHASE 6: Polish, Docs, and Demo (Hours 26 to 34)

- [ ] **T6.1** Full README (Section 9)
- [ ] **T6.2** Architecture diagram exported to `docs/architecture.png`
- [ ] **T6.3** Write `docs/demo-script.md` (Section 8)
- [ ] **T6.4** Run the demo 5 times start to finish, time it, cut anything that drags
- [ ] **T6.5** Record the **demo video** (screen capture plus voiceover, 2 to 3 minutes)
- [ ] **T6.6** Record a **backup live-demo video** in case Wi-Fi or an API fails on stage
- [ ] **T6.7** Test on the presentation laptop and projector resolution
- [ ] **T6.8** Cache a known-good `/readiness` response as an offline fallback
- [ ] **T6.9** Final code cleanup: remove dead code, add docstrings, run linter and formatter
- [ ] **T6.10** Verify `.env` is not in git history. **Rotate keys if it ever was.**
- [ ] **T6.11** Tag a release `v1.0-submission`

---

### PHASE 7: Content Deliverables (parallel, start by Hour 20)

**Mandatory for EVERY team member.** Read the official Hackathon Content Guide first (link is in the original doc).

- [ ] **T7.1** Each member: read the content guide, list their required challenges
- [ ] **T7.2** Each member: write their **Article**
- [ ] **T7.3** Each member: publish their **Social Media post**
- [ ] **T7.4** Each member: record their **Video**
- [ ] **T7.5** Collect all links into one shared doc and into the README
- [ ] **T7.6** Assign ONE person to chase these, since forgetting them is the most common way to lose points

**Content angles worth using (pick different ones per member so the posts do not repeat):**

- "Why audits keep finding the same problems" (problem story)
- "How I used Hindsight retain, recall, and reflect to predict audit findings" (technical)
- "Building an agent that gets smarter from feedback" (learning curve)
- "What I learned generating realistic synthetic compliance data" (data story)
- "Antigravity multi-agent workflow: what worked and what broke" (tooling story)

---

## 7. API Contract (freeze in Phase 0)

Base URL: `http://localhost:8000`

| Method | Path                              | Body                                                                                                  | Returns                                                            |
| ------ | --------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| GET    | `/health`                         | none                                                                                                  | `{ok: true, hindsight: bool, llm: bool}`                           |
| GET    | `/readiness?use_memory=true`      | none                                                                                                  | `ReadinessReport`                                                  |
| POST   | `/ask`                            | `{question: str, use_memory: bool}`                                                                   | `{answer: str, sources: list[str], trace_id: str}` (or SSE stream) |
| POST   | `/feedback`                       | `{flag_id: str, action: "resolved" \| "false_alarm" \| "still_open", evidence_ref?: str, note?: str}` | `{ok: true, new_score: int, explanation: str}`                     |
| GET    | `/memory/trace?trace_id=...`      | none                                                                                                  | `{memories: [{id, text, date, relevance}]}`                        |
| GET    | `/controls/{control_id}/timeline` | none                                                                                                  | `{events: [{date, kind, title, detail}]}`                          |
| POST   | `/demo/reset`                     | none                                                                                                  | `{ok: true}`                                                       |
| GET    | `/eval/curve`                     | none                                                                                                  | `{points: [{interaction, accuracy, score}]}`                       |

Rules:

- All errors return `{error: str, code: str}` with a proper HTTP status
- Every answer and flag carries `sources` that map to real record or memory IDs
- No endpoint may return unsourced claims about findings

---

## 8. Demo Script (3 minutes, memorize this)

**Persona voice:** you are narrating Arjun's morning.

| Time         | Beat       | What is on screen                             | What you say                                                                                                                                                                        |
| ------------ | ---------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0:00 to 0:20 | Hook       | Header: "SOC 2 audit in 30 days"              | "Companies lose enterprise deals without a SOC 2 report. Arjun has 30 days and no idea whether FinPay will pass. Auditors remember every mistake from last year. His team doesn't." |
| 0:20 to 0:50 | Memory OFF | Toggle OFF, ask "Are we ready?"               | "Without memory, the agent gives generic advice: review access controls, check encryption. Useless."                                                                                |
| 0:50 to 1:50 | Memory ON  | Toggle ON, readiness runs, memory panel fills | "Same question, memory on. It found four things Arjun would have missed." Then walk through the four traps, click a source chip on each to show the exact memory                    |
| 1:50 to 2:15 | Prediction | Predictions panel                             | "Using Hindsight reflect across three years, it predicts the auditor will raise access reviews again, and explains why: the reorg that removed the admins."                         |
| 2:15 to 2:40 | Learning   | Click Resolved with evidence on one flag      | "Arjun closes one with evidence. Score jumps from 61 to 68. The flag disappears and the agent explains why." Then show the false-alarm example                                      |
| 2:40 to 3:00 | Close      | Learning curve chart                          | "Most audit findings are repeats. Our agent remembers all of them. Auditors remember everything you got wrong last year. Now your team does too."                                   |

Demo hygiene:

- Call `/demo/reset` before each run
- Pre-warm the backend so the first request is not slow
- Keep a screenshot of every screen as a last-resort fallback
- Rehearse the answers to the tough questions below

### Tough judge questions and answers

- **"Is the data real?"** Real SOC 2 control IDs from an open control set. The company history is synthetic, which the hackathon permits. Validated by script for consistency.
- **"How is this different from Vanta or Drata?"** They monitor current control status. We remember history across years and predict recurrence. We are the memory layer they do not have.
- **"Does the LLM hallucinate findings?"** Detection is rule-based on structured records. The LLM only explains and predicts, and every claim links to a source memory. No source, no claim.
- **"Why memory and not a database?"** A database stores records. Reflect connects patterns across years, like findings clustering after reorgs, without hand-written rules.
- **"What if Hindsight is down?"** The system degrades gracefully, tells the user, and never invents history.
- **"Path to adoption?"** Plug into existing GRC tools and ticketing via connectors. SOC 2 prep is a paid pain point today.

---

## 9. README Outline (Required Deliverable)

- [ ] Title, tagline, and a hero screenshot or GIF
- [ ] **Problem** (3 sentences)
- [ ] **Solution** (3 sentences)
- [ ] **Demo video link** and live demo instructions
- [ ] **How Hindsight memory is used** (REQUIRED section, be specific):
  - what we retain and why (table from Section 3.4)
  - how recall is used and with what queries
  - how reflect is used for prediction
  - how feedback is retained and changes future output
  - before/after memory comparison with screenshots
- [ ] Architecture diagram
- [ ] Learning curve chart plus honest description of how it was measured
- [ ] Data section: sources, what is synthetic, licensing note
- [ ] Setup: prerequisites, env vars, install, seed, run, reset
- [ ] Testing instructions
- [ ] Edge cases and error handling we cover
- [ ] Limitations and roadmap (ISO 27001, real integrations, auth)
- [ ] Team members and roles
- [ ] Links to all content deliverables (articles, posts, videos)
- [ ] License and attribution (Vanta control set, Hindsight)

---

## 10. Team Splits

### 10.1 Two members

|         | Member A: Backend and Memory                                                | Member B: Frontend and Data                                  |
| ------- | --------------------------------------------------------------------------- | ------------------------------------------------------------ |
| Phase 0 | Hindsight and Groq setup, hello-world                                       | Repo, schemas, contract, AGENTS.md                           |
| Phase 1 | Formatter, client wrapper, seed script, smoke test                          | Control selection, data generation, validation, realism pass |
| Phase 2 | All of the agent brain (T2.1 to T2.9)                                       | Design the UI, build static mock with fake data              |
| Phase 3 | All endpoints                                                               | Wire the frontend to `lib/api.ts`                            |
| Phase 4 | Support and bug fixing                                                      | All frontend components                                      |
| Phase 5 | Eval script                                                                 | Chart in UI                                                  |
| Phase 6 | Backup, error handling, tests                                               | README, video, demo script                                   |
| Shared  | Demo rehearsals, content deliverables (each writes their own), final review |                                                              |

Daily 15-minute sync. Agree on the contract in the first hour, then work in parallel.

### 10.2 Five members

| Member | Role                  | Owns                                                                               |
| ------ | --------------------- | ---------------------------------------------------------------------------------- |
| 1      | Memory and Agent Lead | Formatter, seed, detect, predict, reflect prompts. Highest-scoring area.           |
| 2      | Backend and Real-time | FastAPI, SSE, feedback plumbing, LLM retry and fallback layer, tests               |
| 3      | Frontend              | Next.js dashboard, timeline, memory panel, toggle                                  |
| 4      | Data and Evaluation   | Control selection, synthetic data, validation, learning curve eval                 |
| 5      | Demo, Docs, Content   | README, architecture diagram, demo script, video, content deliverable coordination |

Every member still writes their own article, social post, and video.

---

## 11. Risk Register

| Risk                                         | Likelihood | Impact | Mitigation                                                                                |
| -------------------------------------------- | ---------- | ------ | ----------------------------------------------------------------------------------------- |
| Hindsight SDK usage differs from assumptions | Medium     | High   | T0.8 go/no-go, notes in `docs/hindsight-notes.md`, ask in Slack                           |
| Reflect output is vague or generic           | Medium     | High   | Improve memory text richness first, include IDs and dates, tune reflect query wording     |
| Groq function calling errors                 | High       | Medium | Retry, fallback model, JSON repair, avoid depending on tool calls where JSON output works |
| Groq rate limits mid-demo                    | Medium     | High   | Cache a good response, fallback model, backup video                                       |
| Synthetic data feels fake                    | Medium     | High   | Manual realism pass, checklist in 5.4                                                     |
| Compliance topic feels dry                   | High       | Medium | Timeline visual, live score change, strong opening story                                  |
| Agent hallucinated SDK calls (Antigravity)   | High       | Medium | Paste real docs into `docs/`, verify Hindsight calls by hand                              |
| Free tier limits on Antigravity              | Medium     | Medium | Commit often, keep a second model or account ready                                        |
| Live demo Wi-Fi failure                      | Medium     | High   | Backup video, offline cached response, screenshots                                        |
| Forgetting content deliverables              | High       | High   | One owner, deadline before submission, checklist T7.x                                     |
| Secrets leaked to GitHub                     | Low        | High   | `.gitignore`, `.env.example`, check history before submit                                 |
| Scope creep                                  | High       | High   | Non-goals list in 2.4, stretch items cut first                                            |

---

## 12. Antigravity Workflow

### 12.1 Files to write BEFORE dispatching any agent

**AGENTS.md** must contain:

- Stack and versions
- Folder structure from Section 4
- Schemas from Section 3.5
- API contract from Section 7
- Rules: every claim must carry a source ID, never invent history, handle empty recall, never commit secrets, write tests for detection logic
- Hindsight rules: use only methods in `docs/hindsight-notes.md`, never guess SDK signatures

**SPEC.md** must contain:

- Pitch line and persona
- The four traps and the decoy
- The 3-minute demo script
- Definition of done per phase (the exit checks above)

### 12.2 Agent dispatch order

| Order | Agent       | Task                                                        | Mode     |
| ----- | ----------- | ----------------------------------------------------------- | -------- |
| 1     | Data        | Generate and validate synthetic data per Section 5          | Planning |
| 2     | Memory      | Formatter, wrapper, seed, smoke test (Phase 1)              | Planning |
| 3     | Agent brain | Phase 2 tasks, one at a time                                | Planning |
| 4a    | Backend     | Phase 3 routes                                              | Planning |
| 4b    | Frontend    | Phase 4 components (parallel with 4a after contract freeze) | Planning |
| 5     | Eval        | Learning curve script                                       | Fast     |
| 6     | Docs        | README first draft                                          | Fast     |

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

**Product**

- [ ] Memory ON/OFF toggle works and the difference is obvious
- [ ] All four traps detected with correct sources
- [ ] Decoy not flagged
- [ ] Predictions include reasoning and sources
- [ ] Feedback changes the score and the explanation cites it
- [ ] Timeline visual renders for the hero control
- [ ] `/demo/reset` works
- [ ] Errors handled: Hindsight down, LLM malformed output, empty recall

**Submission**

- [ ] GitHub repo public, clean, documented
- [ ] README has the Hindsight usage section
- [ ] Demo video recorded and linked
- [ ] Backup demo video recorded
- [ ] Live demo rehearsed at least 5 times
- [ ] All members: Article done
- [ ] All members: Social post published
- [ ] All members: Video recorded
- [ ] No secrets in git history
- [ ] Release tag created

---

## 14. Time Budget Cheat Sheet

| Block                   | Share of time |
| ----------------------- | ------------- |
| Setup and alignment     | 6%            |
| Data and memory loop    | 18%           |
| Agent brain             | 22%           |
| API layer               | 8%            |
| Frontend                | 20%           |
| Learning curve evidence | 8%            |
| Polish, docs, demo      | 10%           |
| Content deliverables    | 8%            |

**If you fall behind, cut in this order:**

1. Auditor question simulator [STRETCH]
2. Mobile layout
3. SSE streaming (fall back to a plain loading spinner)
4. Extra controls beyond about 15
5. Never cut: memory toggle, memory panel, four traps, feedback loop, README Hindsight section, content deliverables

---

## 15. Success Criteria In One Paragraph

We win if a judge watches 3 minutes and can say: the agent was useless without memory, the agent found four real problems with memory, it cited exactly which past record proved each one, it predicted the next audit's findings from three years of patterns, and it visibly changed its answers after the user gave feedback. Everything in this plan exists to make that sentence true.
