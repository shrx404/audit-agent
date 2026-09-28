# FRONTEND_PLAN.md — AuditMemory MVP
> Goal: Build a polished one-page UI that makes Hindsight memory obvious to judges in under 60 seconds.
> Success: New finding → recurrence analysis → memory evidence → analyst confirm/correct → verified memory retained.
> MVP only: no dashboards, auth, uploads, charts, SSE, or extra frameworks.

## 1. Product Story
AuditMemory is not a generic compliance chatbot.
The UI must make this flow obvious:
```text
New Finding
→ Analyze Against History
→ Possible Recurrence / Not Recurrence
→ Previous Root Cause + Remediation
→ Hindsight Memory Evidence
→ Confirm / Correct / Reject
→ Verified Memory Retained
```
The judge should understand the value without a technical explanation.

## 2. Stack
- Next.js
- TypeScript
- Tailwind CSS
- REST/JSON
- React state only
- Single-page MVP

Required structure:
```text
frontend/src/
├── app/page.tsx
├── components/
│   ├── NewFindingForm.tsx
│   ├── RecurrenceResult.tsx
│   ├── MemoryEvidencePanel.tsx
│   └── ConfirmCorrectPanel.tsx
├── lib/api.ts
└── types/audit.ts
```

## 3. Backend Contract
### POST `/analyze-finding`
Input:
```ts
type NewFindingRequest = {
  control_id: string;
  department: string;
  finding: string;
  evidence_ref?: string | null;
};
```
Response fields:
```ts
type AnalyzeFindingResponse = {
  analysis_id: string;
  status: "suspected";
  possible_recurrence: boolean;
  recurrence_confidence: "low" | "medium" | "high" | null;
  related_past_findings: RelatedFinding[];
  previous_root_cause: PreviousRootCause | null;
  previous_remediation: PreviousRemediation | null;
  explanation: string;
  memories_used: RecalledMemory[];
  deterministic_checks: Flag[];
  warnings: string[];
};
```

### POST `/confirm-finding`
```ts
type ConfirmFindingRequest = {
  analysis_id: string;
  decision: "confirm_recurrence" | "not_recurrence" | "correct";
  linked_finding_ids: string[];
  confirmed_root_cause?: string | null;
  confirmed_remediation?: string | null;
  outcome: "open" | "remediated_with_evidence" | "remediated_no_evidence" | "accepted_risk";
  analyst: string;
  note?: string | null;
};
type ConfirmFindingResponse = {
  ok: boolean;
  trust: "verified";
  retained_mem_ids: string[];
  retrievable: boolean;
  message: string;
};
```
Do not invent frontend-only fields.

## 4. Page Layout
### Header
Show:
- **AuditMemory**
- tagline: `Auditors remember everything you got wrong last year. Your team doesn't.`
- context: `FinPay • SOC 2 Type II`
No full navbar.

### New Finding
Fields:
- Control ID
- Department
- Finding / observation
- Optional evidence reference
CTA: **Analyze Against History**

Optional prefills:
- R1 recurring access-review failure
- R2 same control, different failure
- R1b learning proof

Validation:
- control ID required
- department required
- finding required
- prevent duplicate submit

Loading copy:
- `Searching organizational memory...`
- `Comparing historical failures...`
- `Checking previous root causes...`
No fake percentages.

## 5. Recurrence Result
### Positive
Banner: **Possible Recurrence Detected**
Always show: `Suspected — analyst verification required`
Display:
- confidence
- explanation
- most relevant past finding
- previous root cause
- previous remediation
- remediation outcome
- deterministic checks

### Negative
Banner: **No recurrence detected**
If same-control history exists, show:
`Related, not recurrence`
This is essential for R2.

## 6. Related Past Findings
Each card:
- finding ID
- control ID
- department
- date
- summary
- recurrence candidate / related only
- compact comparison

Comparison dimensions:
1. semantic similarity
2. failure type
3. root cause
4. organizational context
5. previous remediation

Ratings:
- match
- partial
- none
- unknown

## 7. Memory Evidence Panel
This is the hero UI.
Each memory shows:
- memory ID
- type
- date
- trust: Verified
- Current / History
- subject
- memory text
- relevance only if backend provides it

Rules:
- current memory visually stronger
- superseded history visible but muted
- never show AI inference as verified memory

Judge takeaway:
**these exact memories caused this answer.**

## 8. Deterministic Checks
Separate from Hindsight reasoning.
Section: **Direct Compliance Checks**
Possible chips:
- Overdue control test
- Stale remediation ticket
- Missing evidence
Do not imply they came from Hindsight.

## 9. Confirm / Correct
Explain:
**AI analysis remains suspected until an analyst verifies it.**

Editable:
- root cause
- remediation
- outcome
- analyst name
- optional note

Actions:
- **Confirm Recurrence**
- **Correct & Confirm**
- **Not a Recurrence**

After success:
**Verified memory retained**
Show:
- retained memory IDs
- retrievable status
- `Future analyses can now use this confirmed outcome.`

## 10. Required States
### Loading
Disable repeat submit.

### No history
`No relevant organizational history found.`

### Hindsight unavailable
`Historical memory is currently unavailable.`
Do not present recurrence as reliable.

### Backend/LLM error
Clean retry state.

### Retain indexing
If `retrievable=false`:
`Saved; memory indexing is still completing.`

## 11. Visual Direction
Aim for:
- serious enterprise feel
- graphite/dark or clean off-white base
- one accent
- red/amber only for risk
- green for verified/resolved
- strong typography
- subtle borders
- projector-safe sizing
- generous spacing

Avoid:
- neon cyberpunk
- giant gradients
- fake metric cards
- excessive animation
- clutter

The memory evidence is the visual centerpiece.

## 12. Build Order
### F0 — Types + Mock
- [ ] define TS types
- [ ] create `api.ts`
- [ ] create R1 mock
- [ ] render full page with mock data
Exit: whole UX exists without backend.

### F1 — Form
- [ ] fields
- [ ] validation
- [ ] analyze button
- [ ] optional prefills
Exit: form reaches mocked result.

### F2 — Result
- [ ] verdict
- [ ] suspected badge
- [ ] confidence
- [ ] explanation
- [ ] root cause/remediation
- [ ] direct checks
Exit: R1 and R2 clearly differ.

### F3 — Memory Evidence
- [ ] memory cards
- [ ] current/history
- [ ] trust
- [ ] dates
- [ ] superseded styling
Exit: judge can follow evidence trail.

### F4 — Confirmation
- [ ] editable root cause/remediation
- [ ] three analyst actions
- [ ] retained-memory success state
Exit: mock learning flow works.

### F5 — Real API
- [ ] wire `/analyze-finding`
- [ ] wire `/confirm-finding`
- [ ] loading/errors
- [ ] R1 → confirm → R1b
Exit: real end-to-end flow works.

### F6 — Demo Polish
- [ ] projector-safe sizing
- [ ] remove layout jumps
- [ ] rehearse R1/R2/R1b
- [ ] fix only blockers

## 13. Demo Scenarios
### R1 — True recurrence
Input:
`CC6.2`, Support Engineering, monthly access review not performed May–July 2026.
Expected:
- recurrence suspected
- old findings visible
- prior ownership-gap root cause
- failed remediation visible
- current policy shown
- direct checks shown

### R2 — Same control, different failure
Input:
`CC6.2`, contractor granted production admin without manager approval.
Expected:
- not recurrence
- same-control history may appear
- clearly labeled related only

### R1b — Learning proof
Before confirmation:
- older root-cause history used
After correcting/confirming R1:
- new verified memory appears
- root-cause/remediation guidance changes

## 14. Frontend Definition of Done
- [ ] single-page flow works
- [ ] real analyze endpoint connected
- [ ] R1 = possible recurrence
- [ ] R2 = not recurrence
- [ ] Suspected label visible
- [ ] previous root cause shown
- [ ] previous remediation shown
- [ ] recalled memories inspectable
- [ ] current/history visible
- [ ] direct checks separate
- [ ] analyst can confirm/correct/reject
- [ ] retained IDs displayed
- [ ] R1b changes after confirmation
- [ ] empty-history works
- [ ] degraded/error state works
- [ ] demo works without terminal

## 15. Do Not Build in MVP
Do not build:
- readiness score
- prediction panel
- control timeline
- learning curve chart
- AskBox
- memory toggle
- auth
- PDF/file upload
- multi-framework support
- SSE
- giant dashboard
- mobile-first redesign

## 16. Frontend Success Statement
> The judge can see the exact historical memories behind the warning, the AI clearly labels its conclusion as suspected, the analyst can correct it, and the UI shows that confirmed knowledge becoming trusted memory for future analyses.
