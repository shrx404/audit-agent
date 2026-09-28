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
