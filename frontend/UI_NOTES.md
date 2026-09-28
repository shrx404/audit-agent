# Frontend integration handoff

## Run and verify

```sh
npm ci
npm run dev
npm run lint
npm test
npm run build
```

Open http://localhost:3000. The UI uses a 24% / 56% / 20% source explorer, chat, and references layout. Memory is enabled by default and can be changed only in Settings.

## Connect the backend

Create `frontend/.env.local`:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Restart Next.js after changing public environment variables. The backend must allow the frontend origin in its CORS configuration. No provider API keys belong in frontend variables.

All network requests and response validation are isolated in `src/lib/api.ts`. The analysis and confirmation types in `src/types/audit.ts` match `additional info/plan-3.md`. The frontend does not implement Hindsight, detection, or retention.

### Analysis

The UI calls `POST /analyze-finding` with the documented `control_id`, `department`, `finding`, and `evidence_ref`. A small context form obtains required values from the analyst; the UI does not guess their department. Only the currently selected or explicitly named source's content is included (maximum 12,000 characters), never the whole source corpus.

The response uses `analysis_id`, `status: suspected`, `explanation`, `memories_used`, `related_past_findings`, `previous_root_cause`, `previous_remediation`, `deterministic_checks`, and `warnings`. Historical evidence is displayed from the actual response, not from seeded placeholder matches. Source IDs come from `source_id` / `subject` when supplied; otherwise a returned memory is labeled by its actual `mem_id`. The UI does not manufacture filenames, page numbers, confidence percentages, or source locations. Source-index metadata can be mapped in `src/lib/evidence.ts`.

The sidebar displays at most three supported related cases. If fewer are returned, it shows fewer rather than inventing history. Clicking an answer's References button selects its evidence; switching memory off hides historical sidebar evidence.

### Required extension for memory-off behavior

The current documented request has no memory toggle. The backend needs an optional `use_memory: bool = True` on `NewFindingRequest`, advertised in `/openapi.json`. The frontend discovers this field, including ordinary FastAPI `$ref` schemas, and transmits the chosen value. If it is absent, memory-on requests retain the legacy request shape. Memory-off requests are blocked rather than silently invoking historical recall.

When false, the backend must skip Hindsight recall/reflection and all historical match logic. Return empty `memories_used` and `related_past_findings`, no previous historical root cause or remediation, and `possible_recurrence: false`. The UI rejects a memory-off response containing historical context.

For source-only citations, an optional response field is supported:

```ts
references?: {
  source_id: string;
  filename: string;
  category: string;
  snippet: string;
  page?: number;
  lines?: string;
  section?: string;
}[]
```

These are direct references, distinct from recalled `memories_used`. The same optional filename/location fields are supported on recalled memories when the backend has that information. Implement source text retrieval on the backend from the supplied evidence reference for indexed binary files.

### Analyst confirmation

Review & confirm opens an analyst form only on real analysis responses. `POST /confirm-finding` sends the documented decision, linked finding IDs, confirmed root cause/remediation, outcome, analyst, and note. A root cause is required unless the analyst rejects recurrence.

The frontend marks an answer confirmed only when the backend returns `ok: true`, `trust: verified`, nonempty `retained_mem_ids`, `retrievable`, and `message`. It distinguishes confirmed-but-still-indexing from available-for-recall. It never calls confirmation during analysis, never writes directly to Hindsight, and does not simulate new memories. A subsequent query makes a new analysis request, so the backend can return newly retained verified history.

### Source ingestion adapter

No ingestion contract currently exists in the checkout. Upload accepts only `.txt`, `.md`, `.doc`, `.docx`, and `.pdf` (up to 10 MB). Without a connected ingestion route, files remain explicitly not indexed in this browser session. Text files are inspectable locally; binary extraction is left to the backend. No local file is presented as retained history.

When the backend route is ready, configure its actual route and multipart field:

```dotenv
NEXT_PUBLIC_SOURCE_UPLOAD_PATH=/your-actual-ingestion-route
NEXT_PUBLIC_SOURCE_UPLOAD_FIELD=your_actual_file_field
```

The adapter sends one multipart file per request. Its isolated response mapper currently expects `{source_id: string, indexed: true}` to acknowledge completed indexing. Update `AuditApi.upload` to the actual backend response, including an async job/polling flow if necessary; do not treat an accepted upload as indexed. Backend responsibilities are extracting supported document text, registering source IDs, and retaining eligible verified source information into Hindsight. AI analysis speculation must not be retained. A production file-list endpoint and persistence also belong to the backend and can replace `seedSources` without changing the explorer component.

## Seed data and verification limits

`src/lib/sources.ts` presents Markdown views of real records from `src/lib/corpus.json`, originally copied from `backend/data`. These are readable seed records, not uploaded PDFs, not proof of Hindsight indexing, and not recalled memories. The initial chat and references are empty.

Unit tests cover request compatibility, memory-off safeguards, response validation, confirmation acknowledgement, source-backed references, and the related-case limit. They use isolated HTTP response fixtures only inside tests. Real Hindsight recall/retention and the complete learning loop require the backend implementation; they cannot be verified against the current starter script.
