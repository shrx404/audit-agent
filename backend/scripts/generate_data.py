import os
import json
from dotenv import load_dotenv
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.services.llm_client import LLMClient

load_dotenv()
AS_OF_DATE = os.getenv("AS_OF_DATE", "2026-09-28")

def read_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

def write_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def main():
    client = LLMClient()
    
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    controls = read_json(os.path.join(data_dir, "controls.json"))
    findings = read_json(os.path.join(data_dir, "findings.json"))
    remediations = read_json(os.path.join(data_dir, "remediations.json"))
    control_tests = read_json(os.path.join(data_dir, "control_tests.json"))
    staff = read_json(os.path.join(data_dir, "staff.json"))
    
    # Identify controls without findings or tests
    trap_controls = {"CC6.2", "A1.3", "CC9.2", "CC7.1", "CC8.1"}
    available_controls = [c for c in controls if c["id"] not in trap_controls]
    
    print(f"Generating background data for {len(available_controls)} non-trap controls...")
    
    # Ask LLM to generate safe findings and passing control tests
    prompt = f"""
Generate JSON data for an audit compliance system. The output MUST be a JSON object with three keys:
"findings", "remediations", and "control_tests".

Constraints:
1. Controls available: {', '.join([c['id'] for c in available_controls])}
2. Staff available (owners/testers): {', '.join([s['name'] for s in staff if s['active']])}
3. Generate exactly 5 findings. Severity "low" or "medium".
4. Generate exactly 5 remediations, one for each finding. All MUST be status "verified" with an "evidence_ref" (e.g. EV-XXX).
5. Generate exactly 5 control tests, all "passed" and within the required frequency (tested in 2025 or 2026 before {AS_OF_DATE}).
6. Current date is {AS_OF_DATE}.
7. ID formats: Findings (F-YYYY-NN), Remediations (REM-NNN), Evidence (EV-NNN).

Output JSON only.
"""
    print("Calling Groq...")
    try:
        response_text = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response_text)
        
        # Merge
        findings.extend(result.get("findings", []))
        remediations.extend(result.get("remediations", []))
        control_tests.extend(result.get("control_tests", []))
        
        write_json(os.path.join(data_dir, "findings.json"), findings)
        write_json(os.path.join(data_dir, "remediations.json"), remediations)
        write_json(os.path.join(data_dir, "control_tests.json"), control_tests)
        print("Data generated and merged successfully!")
        
    except Exception as e:
        print(f"Failed to generate data: {e}")

if __name__ == "__main__":
    main()
