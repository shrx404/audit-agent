# AuditMemory Backend

## Architecture

AuditMemory is a FastAPI application that integrates with the Hindsight platform to provide contextual, historically grounded insights for SOC 2 audits. It combines deterministic business logic with LLM-powered insights to analyze audit findings, check remediation status, and predict compliance risks.

The application is structured into the following key components:
- **FastAPI Endpoints**: REST endpoints in `main.py` handle user queries, file uploads, and readiness reports.
- **Deterministic Detection (`detect.py`)**: Checks for overdue tests, stale tickets, unverified remediations, and recurring findings using strict business logic instead of LLM interpretation.
- **Hindsight Memory (`memory/client.py`)**: Interacts with the Hindsight API to store and retrieve historical records. 
- **Agent LLM (`agent/ask.py`, `agent/predict.py`)**: Generates structured, conversational insights by synthesizing deterministic flags and retrieved history, ensuring strict data grounding.

## Data Grounding Safeguards

To prevent hallucinations and cross-dataset contamination, AuditMemory enforces the following safeguards:
1. **Strict Source Validation**: The `/ask` endpoint strictly validates every cited record in the LLM's response against the retrieved context from Hindsight or the currently open flags.
2. **Mandatory Abstention**: If the LLM generates hallucinated sources or there is insufficient evidence to confidently answer a query, the agent will abstain rather than guess.
3. **Intent-Specific Response Schema**: The LLM outputs a structured Pydantic schema (with sections for Records, Recurrence, Evidence Gaps, Prediction, and Limitations) before being formatted as a rich Markdown response for the frontend.
4. **Tenant Isolation**: The Hindsight Bank ID is configurable via the `HINDSIGHT_BANK_ID` environment variable (defaulting to `meridian-audit`), isolating query context for the specific tenant.

## Hindsight's Role

Hindsight serves as the long-term memory and contextual engine for the product. While canonical relationships (like open remediations and control mappings) are handled deterministically via local data/databases, Hindsight recall surfaces the qualitative history of controls—such as why a past remediation failed or the historical nuances of a vendor assessment. Hindsight reflection is also used for cross-year pattern prediction, separating forecasts from established facts.