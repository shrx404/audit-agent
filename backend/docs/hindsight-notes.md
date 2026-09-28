# Hindsight API Notes

This document contains findings from the Phase 0 hello-world script (T0.3).

## 1. Client Initialization
- Base URL: `https://api.hindsight.vectorize.io` (Important: `api.hindsight.com` is a parked domain).
- The correct root client method to create a bank is `client.create_bank(bank_id=..., name=...)`, not `client.banks.create(...)`.

## 2. API Responses

### Retain
- Method: `client.retain(bank_id, content, context, timestamp, document_id, retain_async=False)`
- `timestamp` accepts a native Python `datetime` object.
- Response structure: 
  ```python
  RetainResponse(
      success=True, 
      bank_id='finpay-audit', 
      items_count=1, 
      var_async=False, 
      operation_id=None, 
      operation_ids=None, 
      usage=TokenUsage(...)
  )
  ```

### Recall
- Method: `client.recall(bank_id, query)`
- Response structure:
  ```python
  RecallResponse(
      results=[
          RecallResult(
              id='...', 
              type='world', 
              text='SOC 2 auditor raised finding F-2024-03 against control CC6.2 regarding the failure to perform quarterly user access reviews. | When: 2024-03-12 | Involving: SOC 2 auditor | Audit finding with high severity.'
          )
      ], 
      trace=None, 
      entities=None, 
      chunks=None, 
      source_facts=None, 
      source_facts_truncated=None
  )
  ```
- *Observation on Recall fields*: The `RecallResult` has `id`, `type`, and `text`. It does not expose `date` or `score` directly in the top-level repr, but it integrates the `timestamp` and `context` directly into the `text` field (e.g., appended as `| When: 2024-03-12 | ...`).

### Reflect
- Method: `client.reflect(bank_id, query)`
- Response structure:
  ```python
  ReflectResponse(
      text='## Audit Findings Analysis\n...', 
      based_on=None, 
      structured_output=None, 
      structured_output_error=None, 
      usage=TokenUsage(...), 
      trace=None
  )
  ```

## 3. Other Observations
- The client supports synchronous operations (`client.retain`, `client.recall`), but uses `asyncio` under the hood (`Unclosed client session` warnings were visible, which means we might want to manually `.close()` the client if we were in a strict production setting, but for this hackathon it is fine).
- Idempotency with `document_id` wasn't exhaustively tested for deduplication yet, but the parameter is accepted and executed without failure.
- `client.banks.create(...)` fails with `AttributeError`. Use `client.create_bank(...)`.
