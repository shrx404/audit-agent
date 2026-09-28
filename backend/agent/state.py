import json
import os
from typing import Dict, Any, List
from schemas import ReadinessReport, Flag, Prediction

def get_feedback_path() -> str:
    return os.path.join(os.path.dirname(__file__), '..', 'state', 'feedback.json')

def load_feedback() -> Dict[str, Dict[str, Any]]:
    path = get_feedback_path()
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_feedback(data: Dict[str, Dict[str, Any]]):
    path = get_feedback_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def reset_feedback():
    path = get_feedback_path()
    if os.path.exists(path):
        os.remove(path)

def apply_feedback_overlay(report: ReadinessReport, as_of_date_str: str) -> ReadinessReport:
    feedback = load_feedback()
    if not feedback:
        return report

    for flag in report.flags:
        fb = feedback.get(flag.id)
        if fb:
            action = fb['action']
            if action == 'resolved':
                flag.state = 'resolved'
                flag.state_note = f"Closed on {as_of_date_str} with evidence {fb.get('evidence_ref')}"
            elif action == 'false_alarm':
                flag.state = 'false_alarm'
                flag.state_note = f"Marked as false alarm on {as_of_date_str}"
            elif action == 'still_open':
                flag.state = 'open'
                flag.state_note = None

    # Update predictions based on rules
    new_predictions = []
    for p in report.predictions:
        flag = next((f for f in report.flags if f.control_id == p.control_id and f.id in feedback), None)
        if flag:
            fb = feedback[flag.id]
            if fb['action'] == 'resolved':
                # drop likelihood one level
                if p.likelihood == 'high':
                    p.likelihood = 'medium'
                elif p.likelihood == 'medium':
                    p.likelihood = 'low'
                p.reasoning += f" (Note: Risk mitigated by evidence {fb.get('evidence_ref')})"
                new_predictions.append(p)
            elif fb['action'] == 'false_alarm':
                # removed prediction
                pass
            else:
                new_predictions.append(p)
        else:
            new_predictions.append(p)
            
    report.predictions = new_predictions
    return report
