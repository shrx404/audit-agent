import os
from datetime import datetime
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.com")
API_KEY = os.getenv("HINDSIGHT_API_KEY")
BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "finpay-audit")

def main():
    if not API_KEY or API_KEY == "your_hindsight_api_key":
        print("Please set HINDSIGHT_API_KEY in .env")
        return

    print("Initializing Hindsight client...")
    client = Hindsight(base_url=BASE_URL, api_key=API_KEY, timeout=30.0)
    
    print(f"Creating bank {BANK_ID}...")
    try:
        bank = client.create_bank(bank_id=BANK_ID, name="FinPay Audit")
        print(f"Bank created: {bank}")
    except Exception as e:
        print(f"Failed to create bank (or it already exists): {e}")

    print("\nRetaining memory...")
    try:
        ret = client.retain(
            bank_id=BANK_ID,
            content="On 2024-03-12 the SOC 2 auditor raised finding F-2024-03 against control CC6.2 (user access reviews): quarterly access reviews were not performed. Severity: high.",
            context="audit finding",
            timestamp=datetime(2024, 3, 12),
            document_id="F-2024-03",
            retain_async=False
        )
        print(f"Retained: {ret}")
    except Exception as e:
        print(f"Failed to retain (trying ISO format timestamp instead...): {e}")
        try:
            ret = client.retain(
                bank_id=BANK_ID,
                content="On 2024-03-12 the SOC 2 auditor raised finding F-2024-03 against control CC6.2 (user access reviews): quarterly access reviews were not performed. Severity: high.",
                context="audit finding",
                timestamp=datetime(2024, 3, 12).isoformat(),
                document_id="F-2024-03",
                retain_async=False
            )
            print(f"Retained (ISO format worked): {ret}")
        except Exception as inner_e:
            print(f"Failed to retain (ISO format also failed): {inner_e}")

    print("\nRecalling memory...")
    try:
        res = client.recall(bank_id=BANK_ID, query="access review findings")
        print(f"Recall raw result: {res}")
        if hasattr(res, 'results'):
            for r in res.results:
                print(f" - {r.text if hasattr(r, 'text') else r}")
    except Exception as e:
        print(f"Failed to recall: {e}")

    print("\nReflecting...")
    try:
        ans = client.reflect(bank_id=BANK_ID, query="What findings tend to recur and why?")
        print(f"Reflect raw result: {ans}")
        if hasattr(ans, 'text'):
            print(f" - {ans.text}")
    except Exception as e:
        print(f"Failed to reflect: {e}")

if __name__ == "__main__":
    main()
