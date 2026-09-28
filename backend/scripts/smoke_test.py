import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

from memory.client import HindsightWrapper

def run_smoke_test():
    client = HindsightWrapper()
    print("Running Smoke Tests on Hindsight memory...\n")

    # Test 1: access review findings
    print("Test 1: Recall 'access review findings'")
    hits_1 = client.recall("access review findings")
    hits_1_texts = [h.text for h in hits_1[:10]]
    cc62_count = sum(1 for text in hits_1_texts if "CC6.2" in text and "finding" in text.lower())
    print(f"Hits with CC6.2 finding: {cc62_count}")
    assert cc62_count >= 1, "Expected CC6.2 findings in top 10 for 'access review findings'"

    # Test 2: backup restore test
    print("\nTest 2: Recall 'backup restore test'")
    hits_2 = client.recall("backup restore test")
    hits_2_texts = [h.text for h in hits_2[:10]]
    a13_count = sum(1 for text in hits_2_texts if "A1.3" in text and "test" in text.lower())
    print(f"Hits with A1.3 test: {a13_count}")
    assert a13_count >= 1, "Expected A1.3 test in top 10 for 'backup restore test'"

    # Test 3: vendor risk ticket
    print("\nTest 3: Recall 'vendor risk ticket'")
    hits_3 = client.recall("vendor risk ticket")
    hits_3_texts = [h.text for h in hits_3[:10]]
    cc92_count = sum(1 for text in hits_3_texts if "CC9.2" in text and "Ticket" in text)
    print(f"Hits with CC9.2 ticket: {cc92_count}")
    assert cc92_count >= 1, "Expected CC9.2 ticket in top 10 for 'vendor risk ticket'"

    # Test 4: reflect
    print("\nTest 4: Reflect 'What findings tend to recur and why?'")
    reflect_text = client.reflect("What findings tend to recur and why?")
    print("Reflect Result:")
    print(reflect_text)
    assert "access" in reflect_text.lower() or "cc6.2" in reflect_text.lower(), "Expected reflect to mention access reviews"

    print("\nAll Smoke Tests Passed!")

if __name__ == "__main__":
    run_smoke_test()
