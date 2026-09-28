import os
import time
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from hindsight_client import Hindsight

from schemas import MemoryHit

logger = logging.getLogger(__name__)

class MemoryError(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code

class HindsightWrapper:
    _shared_client: Optional[Hindsight] = None

    def __init__(self):
        base_url = os.environ.get("HINDSIGHT_BASE_URL")
        api_key = os.environ.get("HINDSIGHT_API_KEY")
        self.bank_id = os.environ.get("HINDSIGHT_BANK_ID", "finpay-audit")
        
        if not base_url or not api_key:
            raise ValueError("Hindsight configuration missing in environment variables.")
        
        if HindsightWrapper._shared_client is None:
            HindsightWrapper._shared_client = Hindsight(base_url=base_url, api_key=api_key, timeout=30.0)
        self.client = HindsightWrapper._shared_client

    @classmethod
    def close(cls):
        if cls._shared_client is not None:
            try:
                cls._shared_client.close()
            except Exception:
                pass
            cls._shared_client = None

    def _execute_with_retry(self, func, *args, **kwargs):
        attempts = 3
        for attempt in range(attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Attempt to get status code
                status_code = getattr(e, 'status_code', None)
                if status_code is None and hasattr(e, 'response'):
                    status_code = getattr(e.response, 'status_code', None)
                
                if status_code == 401:
                    raise MemoryError("Invalid Hindsight API key", "unauthorized")
                elif status_code == 402:
                    raise MemoryError("Hindsight credits exhausted", "hindsight_credits")
                elif status_code == 404:
                    raise MemoryError("Hindsight bank not found", "not_found")
                elif status_code and status_code >= 400 and status_code < 500:
                    raise MemoryError(f"Hindsight API error: {str(e)}", "bad_request")
                
                # If we get here, it's transient or unhandled
                if attempt == attempts - 1:
                    logger.error(f"Hindsight API failed after {attempts} attempts: {str(e)}")
                    raise MemoryError("Hindsight is currently unavailable", "hindsight_unavailable")
                
                time.sleep(2 ** attempt)

    def create_bank(self, name: str):
        try:
            self._execute_with_retry(self.client.create_bank, bank_id=self.bank_id, name=name)
        except MemoryError as e:
            if e.code == "bad_request" and "already exists" in str(e).lower():
                pass # ignore if it exists
            else:
                raise

    def retain(self, content: str, context: str, timestamp: datetime, document_id: str, retain_async: bool = False):
        self._execute_with_retry(
            self.client.retain,
            bank_id=self.bank_id,
            content=content,
            context=context,
            timestamp=timestamp,
            document_id=document_id,
            retain_async=retain_async
        )

    def recall(self, query: str, session_id: Optional[str] = None) -> List[MemoryHit]:
        res = self._execute_with_retry(
            self.client.recall,
            bank_id=self.bank_id,
            query=query
        )
        
        hits = []
        for r in res.results:
            text = r.text
            # session filter for feedback memories
            if "[session" in text:
                if session_id and f"[session {session_id}]" in text:
                    pass # keep it
                else:
                    continue # filter out feedback from other sessions
            
            # Optionally extract date if it's formatted as "| When: YYYY-MM-DD |"
            # For this hackathon, we keep the raw text which has the date inside it
            # and set date to None on the MemoryHit object, as parsing it might be brittle.
            # The schema allows date to be None.
            
            hits.append(MemoryHit(
                id=r.id,
                text=text,
                date=None,
                relevance=None
            ))
        return hits

    def reflect(self, query: str) -> str:
        res = self._execute_with_retry(
            self.client.reflect,
            bank_id=self.bank_id,
            query=query
        )
        return res.text
