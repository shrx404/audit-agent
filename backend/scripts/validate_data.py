import os
import json
from datetime import datetime

def read_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

def main():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    findings = read_json(os.path.join(data_dir, "findings.json"))
    remediations = read_json(os.path.join(data_dir, "remediations.json"))
    control_tests = read_json(os.path.join(data_dir, "control_tests.json"))
    
    print("Validating data...")
    errors = 0
    
    # Verify dates ordered
    for rem in remediations:
        f = next((f for f in findings if f["id"] == rem["finding_id"]), None)
        if not f:
            print(f"Remediation {rem['id']} points to missing finding {rem['finding_id']}")
            errors += 1
            continue
            
        f_date = datetime.strptime(f["raised_date"], "%Y-%m-%d")
        r_date = datetime.strptime(rem["opened_date"], "%Y-%m-%d")
        if r_date < f_date:
            print(f"Error: Remediation {rem['id']} opened before finding {f['id']} was raised")
            errors += 1
            
        if f["audit_cycle"] != f_date.year:
            print(f"Error: Finding {f['id']} audit cycle {f['audit_cycle']} doesn't match year {f_date.year}")
            errors += 1

    # Check traps exist
    trap_controls = {"CC6.2", "CC9.2", "CC7.1"}
    found_controls = {f["control_id"] for f in findings}
    for tc in trap_controls:
        if tc not in found_controls:
            print(f"Missing trap finding for {tc}")
            errors += 1
            
    test_controls = {t["control_id"] for t in control_tests}
    if "A1.3" not in test_controls:
        print("Missing trap test for A1.3")
        errors += 1
            
    if errors == 0:
        print("Validation passed! All traps present, dates ordered, references valid.")
    else:
        print(f"Validation failed with {errors} errors.")
        exit(1)

if __name__ == "__main__":
    main()
