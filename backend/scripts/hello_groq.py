import os
import json
from dotenv import load_dotenv
import groq

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
PRIMARY_MODEL = os.getenv("LLM_PRIMARY_MODEL", "openai/gpt-oss-120b")
FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "qwen/qwen3.6-27b")

if not API_KEY or API_KEY == "your_groq_api_key":
    print("Please set GROQ_API_KEY in .env")
    exit(1)

def main():
    client = groq.Groq(api_key=API_KEY)
    
    print("Listing models...")
    try:
        models = client.models.list()
        model_ids = [m.id for m in models.data]
        
        print(f"Primary model '{PRIMARY_MODEL}' exists: {PRIMARY_MODEL in model_ids}")
        print(f"Fallback model '{FALLBACK_MODEL}' exists: {FALLBACK_MODEL in model_ids}")

        for model in [PRIMARY_MODEL, FALLBACK_MODEL]:
            if model not in model_ids:
                print(f"\nModel '{model}' is not available in Groq.")
                continue
                
            print(f"\nTesting {model} with JSON output...")
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You output JSON only. The JSON must contain a single key 'status' with value 'ok'."},
                        {"role": "user", "content": "Hello"}
                    ],
                    response_format={"type": "json_object"}
                )
                print(f"{model} response: {response.choices[0].message.content}")
            except Exception as e:
                print(f"{model} failed: {e}")
    except Exception as e:
        print(f"Failed to connect to Groq or list models: {e}")

if __name__ == "__main__":
    main()
