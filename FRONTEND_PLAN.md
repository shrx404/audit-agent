# FRONTEND_PLAN.md — AuditMemory MVP UI

> Goal: Build a polished one-page UI that makes Hindsight memory obvious to judges in under 60 seconds.
> Focus: Strictly UI components, state management, and user flows.

## 1. Product Story & UI Layout
The UI must make the flow obvious: user asks a question, agent consults the source data corpus (if memory is ON), extracts historical context (memory), and responds in the chat.

**Three-Panel Layout:**
1. **Left Panel (Source Data Corpus):** Displays the raw seeded data (Findings, Remediations, Control Tests, Staff, Policies) so the judge can see what the agent *could* know.
2. **Middle Panel (Chat & Timeline):** The main interaction area. Contains the Chat Window (AskBox + Chat History) and a Timeline feature showing the chronological sequence of events for a specific control or finding.
3. **Right Panel (Memory Panel):** Shows the exact recalled memories (with dates, trust, relevance) behind the agent's current answer. This is the hero UI showing *why* the agent answered the way it did.

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
│   ├── layout/Header.tsx
│   ├── left-panel/SourceDataCorpus.tsx
│   ├── middle-panel/ChatWindow.tsx
│   ├── middle-panel/Timeline.tsx
│   └── right-panel/MemoryPanel.tsx
├── lib/api.ts
└── types/audit.ts
```

## 3. Backend Contract (From MVP-PLAN.md)
*Note: All backend logic is handled via these REST endpoints. The frontend only consumes them.*

### API Endpoints
- `GET /health` -> `{ok, hindsight, llm}`
- `GET /readiness` -> `ReadinessReport`
- `POST /ask`
  - Input: `{question: str, use_memory: bool}`
  - Output: `{answer: str, sources: list[str], memories: list[MemoryHit], used_memory: bool}`
- `POST /feedback`
  - Input: `{flag_id: str, action: "resolved" | "false_alarm" | "still_open", evidence_ref?: str, note?: str}`
  - Output: `{ok: true, new_score: int, explanation: str}`
- `POST /demo/reset` -> `{ok: true}`

### Core Types
```ts
type Severity = "low" | "medium" | "high";

interface MemoryHit {
  id: string;
  text: string;
  date: string | null;
  relevance: number | null;
}

interface Flag {
  id: string;
  kind: "repeat_finding" | "overdue_test" | "stale_ticket" | "done_no_evidence";
  control_id: string;
  severity: Severity;
  explanation: string;
  sources: string[];
  memories: MemoryHit[];
  state: "open" | "resolved" | "false_alarm";
  state_note: string | null;
}

interface Prediction {
  control_id: string;
  likelihood: Severity;
  reasoning: string;
  sources: string[];
}

interface ReadinessReport {
  as_of: string;
  audit_start: string;
  score: number; // 0 to 100
  score_breakdown: { flag_id: string; points: number }[];
  flags: Flag[];
  predictions: Prediction[];
  priority_actions: string[];
}
```

## 4. UI Components Detail

### Header
- **AuditMemory Logo/Title**
- **Tagline:** `Auditors remember everything you got wrong last year. Your team doesn't.`
- **Context:** `FinPay • SOC 2 Type II • Audit starts in X days`
- **Memory Toggle:** Big and obvious switch (ON/OFF).

### Left Panel: Source Data Corpus
- A collapsible accordion or tree view of the raw data.
- Categories: `Controls`, `Past Findings`, `Remediation Tickets`, `Control Tests`, `Staff`, `Org Events`.
- Goal: Prove to the judge that the data exists and is realistic.
- Visually clean, mostly read-only JSON or card summaries.

### Middle Panel: Chat Window & Timeline
- **Timeline Feature (New):**
  - A chronological visualization of events (e.g., 2024 Finding -> 2024 Ticket -> 2025 Reorg -> 2026 Overdue Test).
  - Can be triggered by clicking a control ID or flag, or presented inline during chat.
- **Chat History:**
  - Displays user questions and agent answers.
  - Answers include source chips (e.g., `[CC6.2]`, `[REM-118]`).
  - Clicking a source chip highlights the corresponding memory in the Right Panel.
- **AskBox:**
  - Sticky text input at the bottom.
  - Quick-prompt suggestions above the input (e.g., "What findings tend to recur and why?").
  - Sends `use_memory` state with every request.

### Right Panel: Memory Evidence
- **The Hero Visual:** Shows the recalled memories that powered the *last* answer.
- Each memory card shows:
  - Date (prominent)
  - Memory ID
  - Context Tag (e.g., `audit finding`, `user feedback`)
  - The actual memory text.
- If Memory is OFF, this panel shows an empty state: `"Memory disabled. Agent is guessing."`

## 5. Visual Direction
- **Theme:** Serious enterprise feel, graphite/dark or clean off-white base.
- **Colors:** Green for verified/resolved, red/amber for risk.
- **Typography:** Strong, clean (Inter or Roboto).
- **Scale:** Projector-safe sizing (large text for demos).

## 6. Frontend Build Order
1. **F1: Mock Types & API (api.ts)**
2. **F2: Layout Shell (Header, 3 Panels)**
3. **F3: Left Panel (Source Data view)**
4. **F4: Middle Panel (Chat Window & AskBox)**
5. **F5: Middle Panel (Timeline component)**
6. **F6: Right Panel (Memory UI)**
7. **F7: Wire real endpoints (`/ask`, `/readiness`, `/feedback`)**

## 7. Demo Flow (Frontend Perspective)
1. **Memory OFF:** User asks a question, agent gives generic response, Right Panel is empty.
2. **Memory ON:** User asks again, agent gives specific response, Right Panel lights up with exact historical memories.
3. **Timeline:** User clicks a control to see its history plotted chronologically in the middle panel.
4. **Corpus:** User can browse the Left Panel to verify the raw data matches the agent's claims.
