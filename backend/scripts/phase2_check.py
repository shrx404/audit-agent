import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

from agent.core import get_readiness_report
from agent.state import save_feedback, reset_feedback
from agent.ask import ask_agent
from agent.cache import clear_cache
from memory.client import HindsightWrapper
from agent.llm import AgentLLM

def run_phase2_check():
    print("Running Phase 2 Checks...")
    
    # Ensure starting clean
    clear_cache()
    reset_feedback()
    
    print("\nBuilding Readiness Report (this will take a while)...")
    report = get_readiness_report()
    
    # 1. Check exactly 4 flags, no decoy
    assert len(report.flags) == 4, f"Expected 4 flags, got {len(report.flags)}"
    flag_ids = [f.id for f in report.flags]
    assert "repeat_finding:CC6.2" in flag_ids
    assert "overdue_test:A1.3" in flag_ids
    assert "stale_ticket:CC9.2" in flag_ids
    assert "done_no_evidence:CC7.1" in flag_ids
    assert "repeat_finding:CC8.1" not in flag_ids # Decoy
    print("Check 1 Passed: 4 expected flags present, no decoy.")
    
    # 2. Check predictions
    assert len(report.predictions) > 0, "Expected at least 1 prediction"
    print("Check 2 Passed: Predictions generated.")
    
    # 3. memory OFF behavior
    hindsight = HindsightWrapper()
    llm = AgentLLM()
    ans, sources, mems = ask_agent("Are we ready for the audit?", False, report.flags, hindsight, llm)
    assert len(sources) == 0, "Memory OFF should have no sources"
    print("Check 3 Passed: Memory OFF ask has no sources.")
    
    # 4. Feedback loop
    original_score = report.score
    
    # resolved on repeat_finding:CC6.2
    save_feedback({"repeat_finding:CC6.2": {"action": "resolved", "evidence_ref": "EV-902"}})
    report_after_resolve = get_readiness_report()
    assert report_after_resolve.score > original_score, "Score should rise after resolve"
    cc62_flag = next(f for f in report_after_resolve.flags if f.id == "repeat_finding:CC6.2")
    assert cc62_flag.state == "resolved"
    assert "EV-902" in cc62_flag.state_note
    
    cc62_pred = next((p for p in report_after_resolve.predictions if p.control_id == "CC6.2"), None)
    if cc62_pred:
        assert "EV-902" in cc62_pred.reasoning or cc62_pred.likelihood in ["medium", "low"]
        
    print("Check 4 Passed: Resolve raises score and updates prediction.")
    
    # false_alarm on overdue_test:A1.3
    save_feedback({
        "repeat_finding:CC6.2": {"action": "resolved", "evidence_ref": "EV-902"},
        "overdue_test:A1.3": {"action": "false_alarm"}
    })
    report_after_false_alarm = get_readiness_report()
    a13_flag = next(f for f in report_after_false_alarm.flags if f.id == "overdue_test:A1.3")
    assert a13_flag.state == "false_alarm"
    print("Check 5 Passed: False alarm updates state.")
    
    # Reset restores original score
    reset_feedback()
    report_final = get_readiness_report()
    assert report_final.score == original_score, "Reset should restore original score"
    print("Check 6 Passed: Reset restores score.")
    
    print("\nPhase 2 Checks Passed!")

if __name__ == "__main__":
    run_phase2_check()
