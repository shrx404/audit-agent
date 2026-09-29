from datetime import date
from typing import List, Dict, Any, Optional
import json
import os

from schemas import Flag, Severity

def load_json(filename: str) -> List[Dict[str, Any]]:
    path = os.path.join(os.path.dirname(__file__), '..', 'data', filename)
    with open(path, 'r') as f:
        return json.load(f)

def detect_flags(as_of_date: date) -> List[Flag]:
    controls = load_json('controls.json')
    findings = load_json('findings.json')
    remediations = load_json('remediations.json')
    control_tests = load_json('control_tests.json')
    staff = load_json('staff.json')

    staff_active_map = {s['name']: s['active'] for s in staff}
    
    # Map finding to its remediation (assuming 1:1 for simplicity or latest)
    # We sort remediations by opened_date descending to get the latest per finding
    rems_sorted = sorted(remediations, key=lambda x: x['opened_date'], reverse=True)
    rem_by_finding = {}
    for r in rems_sorted:
        if r['finding_id'] not in rem_by_finding:
            rem_by_finding[r['finding_id']] = r

    # Group findings by control
    findings_by_control = {}
    for f in findings:
        cid = f['control_id']
        if cid not in findings_by_control:
            findings_by_control[cid] = []
        findings_by_control[cid].append(f)

    flags = []
    
    # 1. repeat_finding
    for cid, c_findings in findings_by_control.items():
        cycles = set(f['audit_cycle'] for f in c_findings)
        if len(cycles) >= 2:
            # check latest finding
            latest_finding = max(c_findings, key=lambda x: x['raised_date'])
            latest_rem = rem_by_finding.get(latest_finding['id'])
            if not latest_rem or latest_rem['status'] != 'verified':
                flags.append(Flag(
                    id=f"repeat_finding:{cid}",
                    kind="repeat_finding",
                    control_id=cid,
                    severity=latest_finding['severity'],
                    explanation=f"Control {cid} has findings in multiple audit cycles and the latest finding is not verified.",
                    sources=[latest_finding['id'], latest_rem['id'] if latest_rem else cid, cid],
                    memories=[],
                    state="open",
                    state_note=None
                ))

    # 2. overdue_test
    # For overdue_test, we need control tests
    for t in control_tests:
        cid = t['control_id']
        last_tested = date.fromisoformat(t['last_tested'])
        days_since = (as_of_date - last_tested).days
        if days_since > t['required_frequency_days']:
            flags.append(Flag(
                id=f"overdue_test:{cid}",
                kind="overdue_test",
                control_id=cid,
                severity="medium",
                explanation=f"Control {cid} test is overdue by {days_since - t['required_frequency_days']} days.",
                sources=[cid],  # Could add a test ID if we had one
                memories=[],
                state="open",
                state_note=None
            ))

    # 3. stale_ticket & 4. done_no_evidence
    for r in remediations:
        finding = next((f for f in findings if f['id'] == r['finding_id']), None)
        if not finding:
            continue
        cid = finding['control_id']
        
        # stale_ticket
        if r['status'] == 'open':
            opened_date = date.fromisoformat(r['opened_date'])
            days_open = (as_of_date - opened_date).days
            owner_active = staff_active_map.get(r['owner'], False)
            
            if days_open > 180 or not owner_active:
                reason = "open for > 180 days" if days_open > 180 else f"owner {r['owner']} departed"
                flags.append(Flag(
                    id=f"stale_ticket:{cid}",
                    kind="stale_ticket",
                    control_id=cid,
                    severity=finding['severity'],
                    explanation=f"Remediation {r['id']} for control {cid} is stale ({reason}).",
                    sources=[r['id'], finding['id'], cid],
                    memories=[],
                    state="open",
                    state_note=None
                ))
        
        # done_no_evidence
        if r['status'] == 'done' and not r.get('evidence_ref'):
            flags.append(Flag(
                id=f"done_no_evidence:{cid}",
                kind="done_no_evidence",
                control_id=cid,
                severity=finding['severity'],
                explanation=f"Remediation {r['id']} marked done without evidence.",
                sources=[r['id'], finding['id'], cid],
                memories=[],
                state="open",
                state_note=None
            ))

    return flags
