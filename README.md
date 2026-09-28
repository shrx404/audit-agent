# AuditMemory: A Compliance and Audit Agent With Memory

Auditors remember everything you got wrong last year. Your team doesn't. We fix that.

## 🚀 Setup Instructions

### 1. Prerequisites
- **Python 3.11+**
- **[uv](https://github.com/astral-sh/uv)** (Python package manager)

### 2. Environment Configuration
Create a `.env` file in the root of the project by copying the example provided:

```bash
cp .env.example .env
```

Open `.env` and fill in your actual API keys:
- `HINDSIGHT_API_KEY`: Your Hindsight Cloud API Key.
- `GROQ_API_KEY`: Your Groq API Key (starts with `gsk_`, get it from [console.groq.com](https://console.groq.com)).

*Note: Leave `HINDSIGHT_BASE_URL` as `https://api.hindsight.vectorize.io` and `LLM_FALLBACK_MODEL` as `qwen/qwen3.8-27b`.*

## 🧪 Testing the Setup (Phase 0)

To verify that your API keys and connections are working properly, run the two "hello world" scripts from the backend folder:

1. **Test Groq Client**
   This script will verify your Groq API key, list available models, and test a simple JSON-schema extraction with both primary and fallback models.
   ```bash
   cd backend
   uv run .\scripts\groq_hello.py
   ```

2. **Test Hindsight Client**
   This script will create a memory bank (`finpay-audit`), retain a test audit finding, recall it, and have the agent reflect on it.
   ```bash
   cd backend
   uv run .\scripts\hindsight_hello.py
   ```

If both scripts exit without errors and return successful JSON/raw outputs, your local development environment is correctly configured!

## 🚀 Running the API Server (Phase 3)

The backend is built with FastAPI. It provides the core intelligence layer for AuditMemory.

To run the API server locally:
```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

The server will be available at `http://localhost:8000`. You can view the interactive API documentation at `http://localhost:8000/docs`.

### API Endpoints

The API provides the following routes:

- **`GET /health`**
  - **Input**: None
  - **Provides**: Checks and returns the connection status for the Hindsight memory bank and the Groq LLM.
- **`GET /readiness`**
  - **Input**: None
  - **Provides**: Generates and returns the full audit readiness report (flags, scores, predictions).
- **`POST /ask`**
  - **Input**: JSON payload `{"question": "string", "use_memory": boolean}`
  - **Provides**: Queries the audit agent. Returns the AI's `answer`, `sources` used, and relevant `memories`.
- **`POST /feedback`**
  - **Input**: JSON payload `{"flag_id": "string", "action": "string", "evidence_ref": "string" (optional), "note": "string" (optional)}`
  - **Provides**: Submits feedback (e.g. `resolved`, `false_alarm`) for a specific flag. Returns the updated audit score and an explanation of the change.
- **`POST /demo/reset`**
  - **Input**: None
  - **Provides**: Clears all applied feedback and cache, resetting the readiness report to its initial state.

## 🧠 How Hindsight Memory Is Used

AuditMemory uses Hindsight Cloud to store and retrieve historical data, ensuring the agent provides evidence-backed answers instead of generic advice.

### Memory Design
We use one memory bank (`finpay-audit`), retaining one record per call.

| Memory type         | Example content                                                                                                                                                                   | Context tag     |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| Audit finding       | "On 2024-03-12 the SOC 2 auditor raised finding F-2024-03 against control CC6.2 (user access reviews): quarterly access reviews were not performed. Severity: high."              | `audit finding` |
| Remediation ticket  | "Ticket REM-118 opened 2024-03-20, owner Priya Nair, to fix F-2024-03 on control CC6.2. Marked done 2024-06-01. Evidence: EV-311. Status: done, not verified." | `remediation`   |
| Control test        | "Control A1.3 (backup restore test) was last tested 2025-07-28 by Rahul Iyer. Result: passed. Policy requires testing every 365 days."                                            | `control test`  |
| Policy or org event | "On 2024-02-10 the platform team was reorganized and three admins left." | `org event`     |
| User feedback       | "On 2026-09-28 Arjun marked flag repeat_finding:CC6.2 as resolved with evidence EV-902. [session S1]"                                                                             | `user feedback` |

### Core Operations
- **Retain:** Loads the history and every user feedback event asynchronously.
- **Recall:** Pulls the relevant memories for each flagged control and for each question, which are shown in the memory panel.
- **Reflect:** Finds cross-year patterns (e.g. access findings follow team turnover) and feeds the predictions.

### Memory ON vs OFF
Detection uses rules over structured records for precision. Hindsight supplies the evidence, cross-year patterns, and feedback memory. With the toggle OFF, the agent gets none of it and gives generic advice.

## 💾 Data Sources
- Real SOC 2 Control IDs (e.g., CC6.2, CC7.1, A1.3) were used to ground the terminology.
- Synthetic history was generated to build a realistic compliance footprint (remediations, findings, testing logs).

## ⚠️ Limitations
- Only covers the defined MVP scenario. No frameworks beyond SOC 2.
- No live integrations, auth, document uploads, or SSE streaming.
