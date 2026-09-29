from datetime import date
from typing import List, Dict, Any, Optional
import json
import os
import re

from schemas import Flag, Severity

def load_from_uploaded_sources() -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'uploaded_sources.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            sources = json.load(f)
    except:
        return {'controls': [], 'findings': [], 'remediations': [], 'control_tests': [], 'staff': []}

    text = ""
    for s in sources:
        if s.get('title') == 'meridian-audit-dataset.txt':
            text = s.get('content', '')
            break
            
    findings = []
    remediations = []
    tests = []
    staff_set = set()
    staff_inactive = set()

    for b in text.split('---'):
        b = b.strip()
        if not b: continue
        
        if b.startswith('# Finding '):
            fid_m = re.search(r'- Finding ID: (.*)', b)
            cid_m = re.search(r'- Control: (.*)', b)
            cyc_m = re.search(r'- Audit cycle: (.*)', b)
            dt_m = re.search(r'- Raised date: ([^\s]+)', b)
            sev_m = re.search(r'- Severity: (.*)', b)
            if fid_m and cid_m and cyc_m and dt_m:
                sev = sev_m.group(1).strip() if sev_m else 'unknown'
                if sev not in ('low', 'medium', 'high'): sev = 'medium'
                findings.append({
                    'id': fid_m.group(1).strip(),
                    'control_id': cid_m.group(1).strip(),
                    'audit_cycle': cyc_m.group(1).strip(),
                    'raised_date': dt_m.group(1).strip(),
                    'severity': sev
                })
                
        elif b.startswith('# Remediation '):
            rid_m = re.search(r'- Remediation ID: (.*)', b)
            fid_m = re.search(r'- Linked finding: (.*)', b)
            dt_m = re.search(r'- Opened date: ([^\s]+)', b)
            st_m = re.search(r'- Status: (.*)', b)
            own_m = re.search(r'- Owner: ([^(]+)', b)
            ev_m = re.search(r'- Evidence reference: (.*)', b)
            
            if rid_m and fid_m:
                dt = dt_m.group(1).strip() if dt_m else '2023-01-01'
                own = own_m.group(1).strip() if own_m else 'Unknown'
                st = st_m.group(1).strip().lower() if st_m else 'open'
                if 'not verified' in st: st = 'done'
                elif 'verified' in st: st = 'verified'
                elif 'done' in st or 'resolved' in st: st = 'done'
                
                ev = ev_m.group(1).strip() if ev_m else None
                if ev and ('none' in ev.lower() or 'not provided' in ev.lower()):
                    ev = None
                    
                remediations.append({
                    'id': rid_m.group(1).strip(),
                    'finding_id': fid_m.group(1).strip(),
                    'opened_date': dt,
                    'status': st,
                    'owner': own,
                    'evidence_ref': ev
                })
                staff_set.add(own)

        elif b.startswith('# Control Test '):
            cid_m = re.search(r'- Control: (.*)', b)
            dt_m = re.search(r'- Last tested: ([^\s]+)', b)
            freq_m = re.search(r'- Required frequency.*?(\d+)', b)
            if cid_m and dt_m:
                tests.append({
                    'control_id': cid_m.group(1).strip(),
                    'last_tested': dt_m.group(1).strip(),
                    'required_frequency_days': int(freq_m.group(1)) if freq_m else 365,
                    'result': 'pass'
                })
                
        elif b.startswith('# Org Event '):
            left_m = re.search(r'- Description: (.*) left', b)
            if left_m:
                staff_inactive.add(left_m.group(1).strip())

    staff = [{'name': s, 'active': s not in staff_inactive} for s in staff_set]
    return {
        'findings': findings,
        'remediations': remediations,
        'control_tests': tests,
        'staff': staff
    }

def detect_flags(as_of_date: date) -> List[Flag]:
    data = load_from_uploaded_sources()
    findings = data['findings']
    remediations = data['remediations']
    control_tests = data['control_tests']
    staff = data['staff']

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
            # Always flag recurring findings, even if currently verified/done, because they indicate a systemic issue across cycles.
            latest_finding = max(c_findings, key=lambda x: x['raised_date'])
            latest_rem = rem_by_finding.get(latest_finding['id'])
            flags.append(Flag(
                id=f"repeat_finding:{cid}",
                kind="repeat_finding",
                control_id=cid,
                severity=latest_finding['severity'],
                explanation=f"Control {cid} has findings in multiple audit cycles.",
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
                    id=f"stale_ticket:{r['id']}",
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
                id=f"done_no_evidence:{r['id']}",
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
