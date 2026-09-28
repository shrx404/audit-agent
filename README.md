# AuditMemory: Technical Architecture & Implementation

AuditMemory is an intelligent compliance agent built for a SOC 2 Type II audit readiness scenario. It utilizes the Hindsight Cloud API to retain an organization's audit history and injects that state as context into LLM (Groq) reasoning.

## 🛠️ Stack & Architecture

- **Frontend:** Next.js, React, TypeScript, Tailwind. Communicates purely via REST.
- **Backend:** Python 3.11+, FastAPI, Pydantic v2.
- **Memory Engine:** Hindsight Cloud (`hindsight-client` SDK).
- **LLM Engine:** Groq API (`openai/gpt-oss-120b`, fallback: `qwen/qwen3.6-27b`). Structured JSON output verified via Pydantic. No tool calling utilized.

### Architecture Flow
1. **Data Seeding:** Raw JSON records are parsed and injected into Hindsight's vector space via `.retain()`.
2. **Deterministic Rules Engine:** The backend runs local evaluations to flag overdue tests and stale tickets based on an `AS_OF_DATE`.
3. **Retrieval (RAG):** When interacting, the backend issues a `.recall()` against Hindsight to grab relevant history.
4. **Predictive Analytics:** Hindsight's `.reflect()` method is used to extract cross-year patterns (e.g., "reorgs lead to access review failures").
5. **Generation:** Groq synthesizes the `recall` and `reflect` data into structured `Analysis` objects.

---

## 🗄️ Data Model & Schemas

The system relies on strict Pydantic models to validate seeded data before memory ingestion. 

### Core Entities (backend/schemas.py)
- **Finding:** `{ id: str, control_id: str, severity: "low"|"medium"|"high", raised_date: date, auditor_note: str }`
- **Remediation:** `{ id: str, finding_id: str, owner: str, status: "open"|"done"|"verified", opened_date: date, evidence_ref: str|None }`
- **ControlTest:** `{ control_id: str, last_tested: date, result: "passed"|"failed", required_frequency_days: int }`

### Data Seeding Process
Company data resides locally in `backend/data/*.json`. The `seed_memory.py` script performs the following:
1. Validates all entity relationships (e.g., `audit_cycle == raised_date.year`).
2. Compiles entities into flat, human-readable "Memory Texts". Example: *"On 2024-03-12 the SOC 2 auditor raised finding F-2024-03 against control CC6.2. Severity: high."*
3. Pushes these records to the `finpay-audit` bank on Hindsight Cloud using `client.retain()`. Idempotency is maintained via unique `document_id`s.

---

## ⚙️ Detection Engine & Scoring

The backend uses a deterministic rules engine (`detect.py`) to flag issues against a fixed `AS_OF_DATE` constant. It does NOT use the LLM for initial detection, ensuring 100% precision.

### The 4 Detection Traps
1. **`repeat_finding`**: A control has findings in 2 or more distinct audit cycles AND the latest remediation ticket is NOT `verified`.
2. **`overdue_test`**: `(AS_OF_DATE - last_tested).days > required_frequency_days`.
3. **`stale_ticket`**: Remediation `status == open` AND (open > 180 days OR the owner is listed as inactive in `staff.json`).
4. **`done_no_evidence`**: Remediation `status == done` AND `evidence_ref is None`.

### Scoring Formula (`readiness.py`)
- Base Score = 100.
- Deductions apply only to **open** flags: `Score = Score - (kind_weight * severity_multiplier)`.
- **Weights:** `repeat_finding`: 15, `done_no_evidence`: 12, `stale_ticket`: 8, `overdue_test`: 6.
- **Multipliers:** `high`: 1.0, `medium`: 0.7, `low`: 0.4.

---

## 🧠 LLM Integration & Hindsight API Usage

All LLM logic resides in `backend/agent/llm.py` and strictly enforces JSON outputs validated by Pydantic, utilizing exponential backoff for rate limits.

### Hindsight Client Usage
```python
from hindsight_client import Hindsight
client = Hindsight(api_key=API_KEY)

# 1. Retain (Asynchronous ingestion)
client.retain(bank_id="finpay-audit", content="Memory text...", context="audit finding", document_id="F-2024", retain_async=True)

# 2. Recall (Retrieval)
hits = client.recall(bank_id="finpay-audit", query="access review findings")

# 3. Reflect (Cross-year pattern detection)
insight = client.reflect(bank_id="finpay-audit", query="What findings tend to recur and why?")
```

### State & Caching Strategy
Because `.recall()` and `.reflect()` incur network overhead, LLM results are heavily cached in `backend/state/cache.json`.
- State updates (e.g., resolving a flag via `/feedback`) update the local readiness score and the `feedback.json` state dictionary.
- This allows the UI to react instantly while the backend asynchronously retains the feedback event into Hindsight for future learning.

---

## 📡 API Endpoints

- **`GET /health`**: Validates Hindsight and Groq SDK initialization parameters.
- **`GET /readiness`**: Returns `ReadinessReport` containing the deterministic score, active `Flag`s, and reflective `Prediction`s.
- **`POST /ask`**: 
  - Payload: `{"question": "str", "use_memory": bool}`. 
  - Flow: If `use_memory` is true, performs a `.recall()` and attaches `MemoryHit` objects as context. Otherwise, bypasses Hindsight and forces the LLM to give un-sourced generic advice.
- **`POST /feedback`**: 
  - Payload: `{"flag_id": "...", "action": "resolved", "evidence_ref": "EV-..."}`.
  - Flow: Applies feedback instantly, recomputes the score via local state, and returns `{"new_score": int, "explanation": str}`.
- **`POST /analyze-finding`**: 
  - Dedicated endpoint bridging the frontend's strict analysis UI components to the backend. Returns a deeply structured `Analysis` object containing `deterministic_checks` and `memories_used`.

---

## 🚀 Setup Instructions

1. **Install Prerequisites**: Python 3.11+ and Node.js 18+. Install `uv` globally.
2. **Environment**: Run `cp .env.example .env`. Add your `HINDSIGHT_API_KEY` and `GROQ_API_KEY`.
3. **Start Backend**:
   ```bash
   cd backend
   uv pip install -r requirements.txt
   uv run uvicorn main:app --reload --port 8000
   ```
4. **Start Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Access the UI at `http://localhost:3000`.
