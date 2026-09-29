# 🛡️ Audit Agent: The AI-Powered Audit Memory Copilot

In modern enterprise environments, compliance and security auditing is a continuous, labor-intensive, and highly repetitive process. **Audit Agent** is a next-generation AI compliance assistant designed to bridge the gap between static evidence collection and intelligent audit assurance.

---

## 🚨 The Problem Statement & Market Gap

**The Status Quo:**  
Today's auditing workflows are fragmented. Auditors and compliance engineers spend thousands of hours manually reviewing policies, reading SOC 2 reports, and testing controls. Worse, institutional knowledge is lost between audit cycles. When an auditor flags a finding, they often lack the context to know if the exact same issue occurred last year, how it was remediated, or what management’s response was. Current GRC (Governance, Risk, and Compliance) tools act as static filing cabinets, relying entirely on human memory to connect the dots across years of compliance data.

**The Solution:**  
Audit Agent introduces **"Audit Memory"**—an intelligent, stateful retrieval system. Instead of merely searching through documents, Audit Agent acts as a co-pilot that actively remembers past findings, management responses, and historical remediations. When evaluating new evidence, it cross-references past cases to identify recurring issues, deterministic control failures, and root cause patterns, entirely eliminating redundant manual discovery. 

By combining the deterministic reliability required for compliance with the generative flexibility of modern LLMs, Audit Agent significantly accelerates audit cycles, reduces human error, and transforms auditing from a reactive checklist into a proactive, continuous assurance engine.

---

## ✨ Core Features & Differentiators

- **🧠 Stateful Audit Memory**: Unlike standard RAG implementations that just query PDFs, Audit Agent retains distinct "Memories" of past audit findings, management responses, and decisions. It surfaces these autonomously when evaluating new evidence.
- **🔍 Intelligent Source Indexing**: Seamless drag-and-drop ingestion of Policies, Findings, Remediations, and SOC 2 documentation. Documents are chunked, vectorized, and semantically indexed in real-time.
- **📊 Automated Recurrence Detection**: The agent actively compares new evidence against historical records to determine if a vulnerability or control failure is a new issue or a repeat offense.
- **💬 Deterministic Conversational UI**: A responsive, split-pane workspace allowing users to chat with the agent on the left, while instantly verifying the exact document snippets and historical memories the LLM used to generate its conclusion on the right.

---

## 🏗️ Detailed Technical Implementation

Audit Agent is built on a highly decoupled, modern stack designed for high throughput, strict type-safety, and rapid vector retrieval. 

### 1. Frontend Architecture (Next.js & TypeScript)
The user interface is a strictly typed **Next.js 14+** application built with **React** and **Tailwind CSS**.
- **State Management & Workspace**: Implements a complex, resizable multi-pane layout (Source Explorer, Chat Window, Memory/Evidence Panel). State is managed Reactively to allow real-time toggling of Agent Memory.
- **Network Proxying**: Utilizes Next.js `rewrites` in `next.config.ts` to seamlessly proxy frontend API requests (`/api/*`) to the backend FastAPI server, bypassing CORS complexities and ensuring unified domain delivery.
- **Type-Safe API Client**: A robust, custom API wrapper (`AuditApi`) enforces strict schema validation on all incoming JSON responses, ensuring that the frontend only renders properly structured `SourceRecord`, `Analysis`, and `MemoryHit` objects.

### 2. Backend Architecture (FastAPI & Python)
The backend is a high-performance **FastAPI** Python application managed via **`uv`**.
- **Asynchronous Processing**: All endpoints (`/ask`, `/analyze-finding`, `/upload`) utilize non-blocking `async`/`await` patterns for maximum concurrency.
- **Document Processing Pipeline**: Uploaded files (PDF, DOCX, TXT, Markdown) are routed through a robust text-extraction layer (`pypdf`, `python-docx`) before being passed to the vectorization engine.
- **Deterministic Auditing Flags**: Business logic strictly relies on configurable timestamp constraints (e.g., `AS_OF_DATE`) rather than `datetime.now()`. This guarantees reproducible and deterministic audit scoring across identical datasets, a strict requirement for compliance software.

### 3. AI & Vector Engine Integration
The true power of Audit Agent lies in its AI integration, utilizing **Vectorize Hindsight** for memory and **Groq** for high-speed inference.
- **The Hindsight Wrapper (`memory/client.py`)**: The backend implements a custom `HindsightWrapper` class that interfaces with the Vectorize Hindsight API. It handles asynchronous document ingestion, automatic semantic chunking, and contextual memory tagging (e.g., tagging a memory as a "Verified Finding").
- **Structured LLM Inference (Groq + Pydantic v2)**: The agent uses Groq's high-speed inference engine powered by open-source models (e.g., `llama-3.1`). To ensure the LLM never hallucinates JSON structures, the backend enforces **Pydantic v2 schemas** in the LLM tool-calling pipeline. Every answer generated by the agent must carry exact `source_ids` and `memory_ids` that exist in the active index.

---

## Getting Started

### Prerequisites
- **Node.js** (v18+)
- **Python 3.11+**
- **uv** (Fast Python package manager)
- API Keys: **Hindsight** (Vectorize) & **Groq**

### 1. Backend Setup

The backend handles the AI routing, document processing, and Hindsight interactions.

```bash
cd backend

# Install dependencies using uv
uv sync

# Start the FastAPI development server
uv run uvicorn main:app --reload --port 8000
```

**Backend `.env` Configuration:**
Create a `.env` file in the root of the project (or inside `backend/` depending on your setup) containing:
```env
HINDSIGHT_API_KEY=your_hindsight_api_key
GROQ_API_KEY=your_groq_api_key
AS_OF_DATE=2026-09-28
NEXT_PUBLIC_API_URL=/api
```

### 2. Frontend Setup

The frontend provides the interactive Audit Memory workspace.

```bash
cd frontend

# Install dependencies
npm install

# Start the Next.js development server
npm run dev
```

The application will be available at `http://localhost:3000`. 
*(Note: API requests from the frontend are automatically proxied to the backend via Next.js rewrites, so you do not need to configure complex CORS headers).*

---

## 🛠️ Developer Guidelines

- **Strict Typing**: The frontend strictly forbids `any` types. Ensure all API responses conform to the interfaces defined in `types/audit.ts`.
- **No Hallucinations**: When modifying the LLM prompts in `agent/ask.py`, ensure the system prompts strictly forbid inventing history. If the memory engine returns an empty recall, the agent must definitively state "no history found."
- **Secrets Management**: Never commit API keys. The `backend/state/` directory and `.env` files are strictly git-ignored.
