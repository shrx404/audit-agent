from typing import Literal, Optional, List
from pydantic import BaseModel
from datetime import date

Severity = Literal["low", "medium", "high"]

class Staff(BaseModel):
    name: str
    active: bool
    departed_date: Optional[date] = None

class Finding(BaseModel):
    id: str
    control_id: str
    control_name: str
    severity: Severity
    raised_date: date
    audit_cycle: int
    auditor_note: str

class Remediation(BaseModel):
    id: str
    finding_id: str
    owner: str
    opened_date: date
    marked_done_date: Optional[date] = None
    evidence_ref: Optional[str] = None
    status: Literal["open", "done", "verified"]

class ControlTest(BaseModel):
    control_id: str
    last_tested: date
    tester: str
    result: Literal["passed", "failed", "partial"]
    required_frequency_days: int

class MemoryHit(BaseModel):
    id: str
    text: str
    date: Optional[date] = None
    relevance: Optional[float] = None

class Flag(BaseModel):
    id: str
    kind: Literal["repeat_finding", "overdue_test", "stale_ticket", "done_no_evidence"]
    control_id: str
    severity: Severity
    explanation: str
    sources: List[str]
    memories: List[MemoryHit]
    state: Literal["open", "resolved", "false_alarm"]
    state_note: Optional[str] = None

class Prediction(BaseModel):
    control_id: str
    likelihood: Severity
    reasoning: str
    sources: List[str]

class ReadinessReport(BaseModel):
    as_of: date
    audit_start: date
    score: int
    score_breakdown: List[dict]
    flags: List[Flag]
    predictions: List[Prediction]
    priority_actions: List[str]
