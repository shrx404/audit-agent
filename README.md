# Audit Agent

An AI-powered compliance and audit-assurance assistant designed to help auditors, compliance teams, and engineers seamlessly manage, query, and verify audit records, policies, and findings. Audit Agent uses advanced memory retrieval and vector search to act as an intelligent co-pilot for reviewing evidence, tracking exceptions, and comparing past audit cases.

---

## System Workflow

```mermaid
flowchart TD

subgraph group_workspace["Audit workspace"]
  node_page["Workspace<br/>[page.tsx]"]
  node_sources_ui["Source explorer"]
  node_chat_ui["Chat window<br/>[ChatWindow.tsx]"]
  node_memory_ui["Evidence panel<br/>[MemoryPanel.tsx]"]
  node_confirm_ui["Confirmation form"]
  node_api_client["Typed API client<br/>[api.ts]"]
end

subgraph group_backend["Audit workflows"]
  node_api_server["FastAPI routes<br/>[main.py]"]
  node_upload["Evidence ingestion<br/>[main.py]"]
  node_analysis["Finding analysis"]
  node_readiness["Readiness checks<br/>[readiness.py]"]
  node_feedback["Audit feedback<br/>[state.py]"]
end

subgraph group_agent["Agent services"]
  node_ask["Question answering<br/>[ask.py]"]
  node_agent_llm["Structured inference<br/>[llm.py]"]
  node_memory_client["Memory wrapper<br/>[client.py]"]
  node_omniroute_client["OmniRoute client<br/>[llm_client.py]"]
end

subgraph group_integrations["External services"]
  node_hindsight[("Hindsight memory")]
  node_groq{{"Groq inference"}}
  node_omniroute{{"OmniRoute service"}}
end

node_auditor(("Auditor"))

node_auditor -->|"uses"| node_page
node_page -->|"renders"| node_sources_ui
node_page -->|"renders"| node_chat_ui
node_page -->|"renders"| node_memory_ui
node_page -->|"renders"| node_confirm_ui
node_page -->|"requests"| node_api_client
node_api_client -->|"HTTP calls"| node_api_server
node_api_server -->|"handles uploads"| node_upload
node_api_server -->|"answers questions"| node_ask
node_api_server -->|"analyzes findings"| node_analysis
node_api_server -->|"gets readiness"| node_readiness
node_api_server -->|"records feedback"| node_feedback
node_upload -->|"retains evidence"| node_memory_client
node_ask -->|"recalls memories"| node_memory_client
node_ask -->|"generates answer"| node_agent_llm
node_memory_client -->|"reads and writes"| node_hindsight
node_agent_llm -->|"calls model"| node_groq
node_omniroute_client -.->|"routes completions"| node_omniroute
node_omniroute_client -.->|"fallback calls"| node_groq

click node_page "https://github.com/shrx404/audit-agent/blob/main/frontend/src/app/page.tsx"
click node_sources_ui "https://github.com/shrx404/audit-agent/blob/main/frontend/src/components/left-panel/SourceDataCorpus.tsx"
click node_chat_ui "https://github.com/shrx404/audit-agent/blob/main/frontend/src/components/middle-panel/ChatWindow.tsx"
click node_memory_ui "https://github.com/shrx404/audit-agent/blob/main/frontend/src/components/right-panel/MemoryPanel.tsx"
click node_confirm_ui "https://github.com/shrx404/audit-agent/blob/main/frontend/src/components/ConfirmationForm.tsx"
click node_api_client "https://github.com/shrx404/audit-agent/blob/main/frontend/src/lib/api.ts"
click node_api_server "https://github.com/shrx404/audit-agent/blob/main/backend/main.py"
click node_upload "https://github.com/shrx404/audit-agent/blob/main/backend/main.py"
click node_analysis "https://github.com/shrx404/audit-agent/tree/main/backend/agent"
click node_readiness "https://github.com/shrx404/audit-agent/blob/main/backend/agent/readiness.py"
click node_feedback "https://github.com/shrx404/audit-agent/blob/main/backend/agent/state.py"
click node_ask "https://github.com/shrx404/audit-agent/blob/main/backend/agent/ask.py"
click node_agent_llm "https://github.com/shrx404/audit-agent/blob/main/backend/agent/llm.py"
click node_memory_client "https://github.com/shrx404/audit-agent/blob/main/backend/memory/client.py"
click node_omniroute_client "https://github.com/shrx404/audit-agent/blob/main/omniroute/services/llm_client.py"

classDef toneNeutral fill:#f8fafc,stroke:#334155,stroke-width:1.5px,color:#0f172a
classDef toneBlue fill:#dbeafe,stroke:#2563eb,stroke-width:1.5px,color:#172554
classDef toneAmber fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
classDef toneMint fill:#dcfce7,stroke:#16a34a,stroke-width:1.5px,color:#14532d
classDef toneRose fill:#ffe4e6,stroke:#e11d48,stroke-width:1.5px,color:#881337
classDef toneIndigo fill:#e0e7ff,stroke:#4f46e5,stroke-width:1.5px,color:#312e81
classDef toneTeal fill:#ccfbf1,stroke:#0f766e,stroke-width:1.5px,color:#134e4a
class node_page,node_sources_ui,node_chat_ui,node_memory_ui,node_confirm_ui,node_api_client toneBlue
class node_api_server,node_upload,node_analysis,node_readiness,node_feedback toneAmber
class node_ask,node_agent_llm,node_memory_client,node_omniroute_client toneMint
class node_hindsight,node_groq,node_omniroute toneRose
class node_auditor toneIndigo
```

---

## Key Features

| Feature | Description |
| :--- | :--- |
| **Audit Memory & Recall** | Automatically retrieves past findings, management responses, and historical context to intelligently evaluate new audit evidence and avoid redundant work. |
| **Source Explorer** | Upload, browse, and manage policies, access reviews, control definitions, and remediation documents in a centralized UI. |
| **Intelligent Document Indexing** | Integrates seamlessly with the **Vectorize Hindsight API** for powerful real-time document indexing, chunking, and semantic retrieval. |
| **Conversational Interface** | Ask complex, multi-hop questions like *"Which controls had testing exceptions?"* or *"Show me the relationship between SOC 2 requirements and our current policies."* |
| **Case Comparison & Root Cause Analysis** | Leverages LLMs (via Groq) to cross-reference evidence, perform deterministic checks, and highlight recurrence candidates. |

---

## Architecture & Tech Stack

The project is split into two main components: a **Next.js** frontend and a **FastAPI** backend.

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | Next.js (React), TypeScript, Tailwind CSS | Real-time chat UI, resizable side panels for source exploration and memory hits, drag-and-drop file uploads, and deterministic Markdown rendering. |
| **Backend** | FastAPI (Python 3.11+), `uv` | API routing, file processing, memory retention, and interactions with external inference services. |
| **AI / LLM** | Groq, OmniRoute | Fast, structured JSON generation and Pydantic v2 validation via fallback chains. |
| **Vector Engine** | Hindsight API | `hindsight-client` by Vectorize for semantic search and operational memory. |

---

## Getting Started

### Prerequisites

| Prerequisite | Minimum Version | Notes |
| :--- | :--- | :--- |
| **Node.js** | v18+ | Required for the Next.js frontend. |
| **Python** | 3.11+ | Required for the FastAPI backend. |
| **Package Manager** | `uv` | Fast Python package manager. |
| **API Keys** | - | **Hindsight API Key** (Vectorize) and **Groq API Key**. |

### 1. Backend Setup

The backend handles API routing, file processing, and interactions with Hindsight and Groq.

```bash
cd backend

# Install dependencies using uv
uv sync

# Start the FastAPI server (runs on http://localhost:8000)
uv run uvicorn main:app --reload --port 8000
```

**Backend Environment Variables:**
Create a `.env` file inside the `backend/` directory (these should NEVER be committed to Git):
```env
HINDSIGHT_API_KEY=your_hindsight_api_key
GROQ_API_KEY=your_groq_api_key
```

### 2. Frontend Setup

The frontend provides the interactive Audit Memory workspace.

```bash
cd frontend

# Install dependencies
npm install
# or if using yarn/pnpm: yarn install

# Start the development server (runs on http://localhost:3000)
npm run dev
```

**Frontend Environment Variables:**
Create a `.env.local` file inside the `frontend/` directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SOURCE_UPLOAD_PATH=/upload
```

---

## Usage Guide

| Step | Action | Description |
| :--- | :--- | :--- |
| **1. Launch** | Open Workspace | Navigate to `http://localhost:3000` in your browser. |
| **2. Add Evidence** | Upload Files | Use the **Source Explorer** (left panel) to drag and drop audit evidence (PDFs, TXT, JSON, MD). Files are immediately indexed into your Hindsight corpus. |
| **3. Ask Questions** | Chat Interface | Ask compliance-related queries in the central chat panel. Ensure **Agent Memory** is toggled ON to reference historical cases. |
| **4. Review Context** | Inspect Memory Hits | The right panel displays the precise references, exact document snippets, and historical findings the agent used to formulate its answer. |
| **5. Confirm Findings** | Evaluate Comparisons | Review LLM-generated comparisons and confirm whether an issue is a recurrence of a past finding. |

---

## API Reference (Backend)

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/sources` | `GET` | Fetches the combined list of locally seeded documents and live documents indexed in the Hindsight online corpus. |
| `/upload` | `POST` | Uploads a document (TXT, MD, PDF, etc.) to the local index and forwards it to Hindsight for vector embedding. |
| `/api/ask` | `POST` | The main conversational endpoint. Submits the user's question along with context and memory flags to the LLM. |

---

## Development Guidelines

- **Package Management**: Always use `uv` for managing Python dependencies to ensure speed and determinism.
- **Type Safety**: The frontend strictly uses TypeScript. Avoid `any` types; prefer strict interfaces (e.g., `SourceRecord`, `Analysis`, `MemoryHit`).
- **Secrets Management**: Never commit API keys. Use `.env` files and keep the `backend/state/` directory gitignored.
- **Business Logic**: Never use `date.today()` or `datetime.now()` for audit constraints. Rely on `AS_OF_DATE` configurations for reproducible deterministic auditing.

---

*Built for advanced agentic auditing.*
