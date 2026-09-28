import os
import json
from datetime import datetime
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.com")
API_KEY = os.getenv("HINDSIGHT_API_KEY")
BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "finpay-audit")

if not API_KEY or API_KEY == "your_hindsight_api_key":
    print("Please set HINDSIGHT_API_KEY in .env")
    exit(1)

def main():
    print("Connecting to Hindsight...")
    client = Hindsight(base_url=BASE_URL, api_key=API_KEY, timeout=30.0)
    
    print(f"Creating bank: {BANK_ID}")
    try:
        bank_res = client.banks.create(bank_id=BANK_ID, name="FinPay Audit")
        print(f"Bank creation result: {bank_res}")
    except Exception as e:
        print(f"Bank creation failed (might already exist): {e}")

    print("\nRetaining memory...")
    try:
        retain_res = client.retain(
            bank_id=BANK_ID,
            content="On 2024-03-12 the SOC 2 auditor raised finding F-2024-03 against control CC6.2 (user access reviews): quarterly access reviews were not performed.",
            context="audit finding",
            timestamp=datetime(2024, 3, 12).isoformat(),
            document_id="F-2024-03",
            retain_async=False
        )
        print(f"Retain result: {retain_res}")
    except Exception as e:
        print(f"Retain failed: {e}")

    print("\nRecalling memory...")
    try:
        recall_res = client.recall(bank_id=BANK_ID, query="access review findings")
        print("Recall result:")
        for r in recall_res.results:
            print(f" - {r.text} (ID: {r.id}, Date: {getattr(r, 'date', 'N/A')}, Relevance: {getattr(r, 'relevance', 'N/A')})")
    except Exception as e:
        print(f"Recall failed: {e}")

    print("\nReflecting...")
    try:
        reflect_res = client.reflect(bank_id=BANK_ID, query="What findings tend to recur and why?")
        print(f"Reflect result: {reflect_res.text}")
    except Exception as e:
        print(f"Reflect failed: {e}")

if __name__ == "__main__":
    main()
