from typing import Dict, Any, Optional

def format_finding(finding: Dict[str, Any]) -> str:
    """Format an audit finding into memory text."""
    date = finding["raised_date"]
    id_ = finding["id"]
    control_id = finding["control_id"]
    control_name = finding["control_name"]
    note = finding["auditor_note"]
    severity = finding["severity"]
    return f"On {date} the SOC 2 auditor raised finding {id_} against control {control_id} ({control_name}): {note}. Severity: {severity}."

def format_remediation(ticket: Dict[str, Any], control_id: str) -> str:
    """Format a remediation ticket into memory text."""
    id_ = ticket["id"]
    opened = ticket["opened_date"]
    owner = ticket["owner"]
    finding_id = ticket["finding_id"]
    marked_done = ticket.get("marked_done_date")
    evidence = ticket.get("evidence_ref")
    status = ticket["status"]
    
    text = f"Ticket {id_} opened {opened}, owner {owner}, to fix {finding_id} on control {control_id}."
    if marked_done:
        text += f" Marked done {marked_done}."
    if evidence:
        text += f" Evidence: {evidence}."
    text += f" Status: {status}."
    return text

def format_control_test(test: Dict[str, Any], control_name: str) -> str:
    """Format a control test into memory text."""
    control_id = test["control_id"]
    last_tested = test["last_tested"]
    tester = test["tester"]
    result = test["result"]
    freq = test["required_frequency_days"]
    return f"Control {control_id} ({control_name}) was last tested {last_tested} by {tester}. Result: {result}. Policy requires testing every {freq} days."

def format_org_event(event: Dict[str, Any]) -> str:
    """Format an org event into memory text."""
    date = event["date"]
    desc = event["description"]
    return f"On {date} {desc}."

def format_policy_change(policy: Dict[str, Any]) -> str:
    """Format a policy change into memory text."""
    date = policy["date"]
    desc = policy["description"]
    return f"On {date} {desc}."

def format_staff_departure(staff: Dict[str, Any]) -> str:
    """Format staff departure into memory text."""
    date = staff["departed_date"]
    name = staff["name"]
    return f"On {date} {name} left Meridian."

def format_user_feedback(date: str, flag_id: str, action: str, evidence_ref: Optional[str], session_id: str) -> str:
    """Format user feedback into memory text."""
    evidence_text = f" with evidence {evidence_ref}" if evidence_ref else ""
    return f"On {date} Arjun marked flag {flag_id} as {action}{evidence_text}. [session {session_id}]"
