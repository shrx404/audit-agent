import os
from datetime import date, timedelta
from typing import Tuple

from schemas import ReadinessReport
from agent.detect import detect_flags
from agent.readiness import calculate_score
from agent.predict import generate_predictions
from agent.state import apply_feedback_overlay, reset_feedback
from agent.cache import load_cached_report, save_cached_report, clear_cache
from memory.client import HindsightWrapper
from agent.llm import AgentLLM

def get_as_of_date() -> date:
    d_str = os.environ.get("AS_OF_DATE", "2026-09-28")
    return date.fromisoformat(d_str)

def build_readiness_report() -> ReadinessReport:
    """Builds the report from scratch (slow, uses LLM/Hindsight)."""
    as_of = get_as_of_date()
    audit_start = as_of + timedelta(days=30)
    
    flags = detect_flags(as_of)
    hindsight = HindsightWrapper()
    llm = AgentLLM()
    
    predictions = generate_predictions(flags, hindsight, llm)
    score, breakdown = calculate_score(flags)
    
    report = ReadinessReport(
        as_of=as_of,
        audit_start=audit_start,
        score=score,
        score_breakdown=breakdown,
        flags=flags,
        predictions=predictions,
        priority_actions=["Resolve high severity findings", "Update missing evidence"]
    )
    return report

def get_readiness_report() -> ReadinessReport:
    """Gets the report, either from cache or building it, then applies feedback."""
    report = load_cached_report()
    if not report:
        report = build_readiness_report()
        save_cached_report(report)
        
    # Always apply current feedback to a fresh copy
    report_copy = report.model_copy(deep=True)
    report_copy = apply_feedback_overlay(report_copy, str(get_as_of_date()))
    
    # Recalculate score after feedback
    score, breakdown = calculate_score(report_copy.flags)
    report_copy.score = score
    report_copy.score_breakdown = breakdown
    
    return report_copy
