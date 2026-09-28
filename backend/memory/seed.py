import json
import os
from datetime import datetime
from memory.client import HindsightWrapper
from memory.formatter import (
    format_finding, format_remediation, format_control_test,
    format_org_event, format_policy_change, format_staff_departure
)

def load_json(filename: str):
    filepath = os.path.join(os.path.dirname(__file__), '..', 'data', filename)
    with open(filepath, 'r') as f:
        return json.load(f)

def seed_memory():
    client = HindsightWrapper()
    client.create_bank("FinPay Audit")

    controls = {c["id"]: c["name"] for c in load_json("controls.json")}
    findings = load_json("findings.json")
    remediations = load_json("remediations.json")
    control_tests = load_json("control_tests.json")
    org_events = load_json("org_events.json")
    policy_changes = load_json("policy_changes.json")
    staff = load_json("staff.json")

    print(f"Seeding memories to Hindsight for bank: {client.bank_id}")

    # Retain findings
    for f in findings:
        text = format_finding(f)
        date_obj = datetime.strptime(f["raised_date"], "%Y-%m-%d")
        client.retain(
            content=text,
            context="audit finding",
            timestamp=date_obj,
            document_id=f["id"],
            retain_async=False
        )
        print(f"Retained finding: {f['id']}")

    # Retain remediations
    # Need control_id for remediations
    finding_map = {f["id"]: f["control_id"] for f in findings}
    for r in remediations:
        control_id = finding_map.get(r["finding_id"], "Unknown")
        text = format_remediation(r, control_id)
        date_obj = datetime.strptime(r["opened_date"], "%Y-%m-%d")
        client.retain(
            content=text,
            context="remediation",
            timestamp=date_obj,
            document_id=r["id"],
            retain_async=False
        )
        print(f"Retained remediation: {r['id']}")

    # Retain control tests
    for t in control_tests:
        c_name = controls.get(t["control_id"], "")
        text = format_control_test(t, c_name)
        date_obj = datetime.strptime(t["last_tested"], "%Y-%m-%d")
        # generate a stable ID since tests might not have one
        doc_id = f"TEST-{t['control_id']}-{t['last_tested']}"
        client.retain(
            content=text,
            context="control test",
            timestamp=date_obj,
            document_id=doc_id,
            retain_async=False
        )
        print(f"Retained test: {doc_id}")

    # Retain org events
    for i, e in enumerate(org_events):
        text = format_org_event(e)
        date_obj = datetime.strptime(e["date"], "%Y-%m-%d")
        doc_id = f"ORG-{e['date']}-{i}"
        client.retain(
            content=text,
            context="org event",
            timestamp=date_obj,
            document_id=doc_id,
            retain_async=False
        )
        print(f"Retained org event: {doc_id}")

    # Retain policy changes
    for i, p in enumerate(policy_changes):
        text = format_policy_change(p)
        date_obj = datetime.strptime(p["date"], "%Y-%m-%d")
        doc_id = f"POL-{p['date']}-{i}"
        client.retain(
            content=text,
            context="policy change",
            timestamp=date_obj,
            document_id=doc_id,
            retain_async=False
        )
        print(f"Retained policy change: {doc_id}")

    # Retain staff departures
    for i, s in enumerate(staff):
        if not s["active"] and s.get("departed_date"):
            text = format_staff_departure(s)
            date_obj = datetime.strptime(s["departed_date"], "%Y-%m-%d")
            doc_id = f"DEP-{s['name'].replace(' ', '')}-{s['departed_date']}"
            client.retain(
                content=text,
                context="org event",
                timestamp=date_obj,
                document_id=doc_id,
                retain_async=False
            )
            print(f"Retained departure: {doc_id}")

    print("Memory seeding complete.")
