import os
import sys
from datetime import date
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.detect import detect_flags

def test_deterministic_checks():
    as_of = date.fromisoformat("2026-09-28")
    flags = detect_flags(as_of)
    flag_ids = [f.id for f in flags]

    # CTRL-005 and CTRL-016 recurring findings
    assert "repeat_finding:CTRL-005" in flag_ids
    assert "repeat_finding:CTRL-016" in flag_ids

    # Overdue CTEST-004
    assert "overdue_test:CTEST-004" in flag_ids

    # Remediations marked done without evidence
    assert "done_no_evidence:CTRL-103" in flag_ids # REM-003
    assert "done_no_evidence:CTRL-106" in flag_ids # REM-006
    assert "done_no_evidence:CTRL-101" in flag_ids # REM-P01

    # Open tickets with departed owners
    assert "stale_ticket:CTRL-200" in flag_ids

    # Verified decoy FIND-007 / REM-007 should NOT be flagged
    assert "repeat_finding:CTRL-007" not in flag_ids
    assert "stale_ticket:CTRL-007" not in flag_ids
    assert "done_no_evidence:CTRL-007" not in flag_ids

    # CC6.2 recurring finding because latest is not verified
    assert "repeat_finding:CC6.2" in flag_ids

def test_ask_agent_grounding():
    from agent.ask import ask_agent
    from schemas import MemoryHit
    
    class MockHindsight:
        def __init__(self):
            self.bank_id = "meridian-audit"
        def recall(self, q):
            return [MemoryHit(id="MEM-123", text="Actual history about access", date=None, relevance=None)]
    
    class MockLLM:
        def generate_json(self, prompt, context, response_format):
            class MockRes:
                answer = "Fake answer"
                records = None
                recurrence = None
                evidence_gaps = None
                prediction = None
                limitations = None
                sources = ["FAKE-SRC-999"] # Not in memory
                def model_dump_json(self):
                    return "{}"
            return MockRes()
            
    hindsight = MockHindsight()
    llm = MockLLM()
    
    answer, sources, memories = ask_agent("What is our status?", True, [], hindsight, llm)
    assert "insufficient evidence" in answer
    assert sources == []

