import os
import sys

# Ensure backend package can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from dotenv import load_dotenv
from backend.services.llm_client import LLMClient

def test_integration():
    # Load environment variables
    dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    load_dotenv(dotenv_path)
    
    print("Testing local integration...")
    try:
        client = LLMClient()
        print(f"Is OmniRoute configured? {client.is_omniroute}")
        print(f"Model used: {client.model}")
        
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Reply exactly with: integration works"}]
        )
        print(f"Response: {response}")
        print("Integration test passed!")
    except Exception as e:
        print(f"Integration test failed: {e}")

if __name__ == "__main__":
    test_integration()
