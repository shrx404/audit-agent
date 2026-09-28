# AuditMemory: The Compliance & Audit Agent with Hindsight

![AuditMemory Banner](https://via.placeholder.com/1200x300?text=AuditMemory+-+Compliance+With+Hindsight)

> *"Auditors remember everything you got wrong last year. Your team doesn't. We fix that."*

## 📖 Problem Statement

In the world of enterprise compliance frameworks like SOC 2 and ISO 27001, history inevitably repeats itself. Organizations often fail audits not because they are ignorant of the rules, but because their institutional memory fades. Key team members depart, ticketing systems become overly complex and cluttered, and last year's auditor findings are buried in spreadsheets. 

When the next audit cycle rolls around, the very same mistakes resurface. These recurring findings lead to costly exceptions, prolonged remediation cycles, and loss of customer trust. Existing Governance, Risk, and Compliance (GRC) tools are fundamentally flawed: they focus on tracking static controls in the present moment, completely lacking the contextual, historical awareness required to understand *why* a control is failing or if it represents a deeply ingrained organizational pattern.

## 💡 The Solution

**AuditMemory** is a next-generation, intelligent compliance agent that utilizes AI and **Hindsight Cloud** to completely retain an organization's audit history. It acts as a tireless, omnipresent compliance manager that remembers every single finding, remediation ticket, control test, and organizational event.

Instead of providing generic compliance advice, AuditMemory delivers highly contextual, evidence-backed insights:
- **Proactive Trap Detection:** Automatically flags recurring issues, overdue tests, stale tickets, and missing evidence long before the auditor arrives.
- **Intelligent Predictive Findings:** Utilizes cross-year historical patterns (e.g., a platform reorg immediately followed by access review failures) to predict exactly what an auditor is likely to flag.
- **Continuous Learning Loop:** Incorporates user feedback instantly. If a compliance manager provides evidence to resolve a flag, the agent immediately learns from this, updates the memory graph, and adjusts the compliance readiness score in real-time.

---

## 🛠️ Tech Stack & Architecture

- **Frontend:** Next.js, React, TypeScript, Tailwind CSS
- **Backend:** Python 3.11+, FastAPI, Pydantic v2
- **Memory Infrastructure:** Hindsight Cloud (`hindsight-client` Python SDK)
- **Large Language Model:** Groq (`openai/gpt-oss-120b` & `qwen/qwen3.6-27b`)
- **Package Manager:** `uv`

AuditMemory operates on a microservice architecture where the Next.js frontend interacts strictly via REST with the FastAPI backend. The backend orchestrates interactions between the LLM (for reasoning) and Hindsight Cloud (for historical context and memory retrieval).

---

## 🚀 Setup & Installation

### 1. Prerequisites
- **Python 3.11+** installed on your system.
- **[uv](https://github.com/astral-sh/uv)** (Fast Python package manager).
- **Node.js 18+** for the frontend UI.

### 2. Environment Configuration
Create a `.env` file in the root of the project by copying the provided example:

```bash
cp .env.example .env
```

Open `.env` and fill in your API keys:
- `HINDSIGHT_API_KEY`: Your Hindsight Cloud API Key.
- `GROQ_API_KEY`: Your Groq API Key (get it from [console.groq.com](https://console.groq.com)).

*(Note: Leave `HINDSIGHT_BASE_URL` as `https://api.hindsight.vectorize.io`)*

### 3. Running the Backend
The backend runs on FastAPI and acts as the intelligence layer.
```bash
cd backend
uv pip install -r requirements.txt
uv run uvicorn main:app --reload --port 8000
```
*The server will be available at `http://localhost:8000`. API documentation is at `http://localhost:8000/docs`.*

### 4. Running the Frontend
The frontend is a polished, single-page Next.js application designed for enterprise demos.
```bash
cd frontend
npm install
npm run dev
```
*The UI will be available at `http://localhost:3000`.*

---

## 🧠 How Hindsight Memory Is Used

AuditMemory leverages Hindsight Cloud to store and retrieve historical data, ensuring the agent provides **evidence-backed answers** instead of generic advice. 

### Memory Design
We use one centralized memory bank (`finpay-audit`), retaining one precise record per API call.

| Memory Type         | Example Content | Context Tag |
| ------------------- | ----------------| ----------- |
| **Audit finding**   | "On 2024-03-12 the SOC 2 auditor raised finding F-2024-03 against control CC6.2..." | `audit finding` |
| **Remediation**     | "Ticket REM-118 opened 2024-03-20 to fix F-2024-03. Marked done. Evidence: EV-311." | `remediation`   |
| **Control test**    | "Control A1.3 last tested 2025-07-28 by Rahul Iyer. Result: passed." | `control test`  |
| **Org event**       | "On 2024-02-10 the platform team was reorganized and three admins left." | `org event`     |
| **User feedback**   | "On 2026-09-28 user resolved flag repeat_finding:CC6.2 with evidence EV-902." | `user feedback` |

### Core Operations
- **Retain:** The backend asynchronously retains every piece of company history and real-time user feedback into Hindsight, vectorizing it for immediate retrieval.
- **Recall:** When a user asks a question, the backend queries Hindsight to pull relevant memories for flagged controls. This context is injected directly into the LLM prompt.
- **Reflect:** Discovers deep, cross-year patterns (e.g., access findings typically follow team turnover) to feed predictive analytics.

### Memory ON vs. OFF
You can toggle the agent's memory directly in the UI header. 
- **Memory ON:** Hindsight supplies historical evidence, cross-year patterns, and feedback memory. 
- **Memory OFF:** The agent receives absolutely no historical context and is forced to give generic, unhelpful advice—perfectly demonstrating the value of Hindsight Memory.

---

## 🗄️ Company Data: How It Is Provided & Stored

In AuditMemory, providing realistic company data is paramount. The agent operates strictly on a simulated "Source of Truth" dataset representing a fictional fintech company, **FinPay**.

### 1. Where the Data Originates
Company data is seeded via highly realistic **JSON files** stored locally in `backend/data/`. These files represent the raw exports you would typically get from Jira, Workday, or a GRC platform:
- `controls.json`: The active SOC 2 controls.
- `findings.json`: Past auditor findings across multiple years.
- `remediations.json`: The tickets created to address those findings.
- `control_tests.json`: Logs of internal compliance testing.
- `staff.json` / `org_events.json`: Team structure, turnover, and major reorgs.

### 2. How the Data is Stored and Processed
1. **Initial Seeding:** When the application is initialized, a seeding script (`seed_memory.py`) reads these static JSON files.
2. **Formatting for Hindsight:** The data is transformed into structured, natural language "Memory Texts" (e.g., parsing a raw JSON remediation object into a human-readable string summarizing the ticket).
3. **Retention to Hindsight Cloud:** These formatted memory texts are then pushed to Hindsight Cloud via the `client.retain()` API. 
4. **Local State Cache:** User feedback actions (like resolving a flag in the UI) are stored locally in a temporary `backend/state/feedback.json` to immediately adjust the readiness score, while simultaneously being asynchronously retained in Hindsight for long-term agent learning.

---

## 📡 API Reference

The FastAPI backend exposes several strictly-typed endpoints that power the frontend application. 

- **`GET /health`**
  Checks and returns the connection status for the Hindsight memory bank and the Groq LLM. Ensures the core infrastructure is responsive.
- **`GET /readiness`**
  Generates and returns the full audit readiness report. This includes the computed compliance score, active risk flags (calculated deterministically), and predictions generated by Hindsight's `Reflect` API.
- **`POST /ask`**
  Queries the audit agent. The payload includes `use_memory: boolean`. If true, the agent uses Hindsight's `Recall` to fetch historical context before querying the Groq LLM. Returns the `answer`, `sources`, and exact `memories` cited.
- **`POST /feedback`**
  Submits user feedback (e.g. `resolved`, `false_alarm`) for a specific flag. This requires an `evidence_ref`. Returns the updated audit score and retains this action in memory.
- **`POST /demo/reset`**
  Clears all applied feedback and local state cache, completely resetting the readiness report to its initial state for a fresh demo.
- **`POST /analyze-finding`** & **`POST /confirm-finding`**
  Specialized endpoints built to seamlessly map the frontend's highly structured analysis UI to the backend's Hindsight memory logic. Returns deeply structured `Analysis` objects containing related past findings, memories used, and deterministic checks.

---

## ⚠️ Limitations (MVP Scope)
- **Framework Focus:** Only covers the defined MVP scenario (SOC 2 Type II readiness). It does not currently support ISO 27001 or GDPR out-of-the-box.
- **Authentication:** The current build prioritizes a seamless demo flow over multi-tenant architectures (no live SSO/auth).
- **Data Ingestion:** Document parsing and live ingestion via the frontend UI is mocked for the MVP. All real historical data is securely seeded via the backend pipeline scripts.
