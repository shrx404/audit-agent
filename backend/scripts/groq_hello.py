import os
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

API_KEY = os.getenv("GROQ_API_KEY")
PRIMARY_MODEL = os.getenv("LLM_PRIMARY_MODEL", "openai/gpt-oss-120b")
FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "qwen/qwen3.6-27b")

class ExampleSchema(BaseModel):
    message: str
    confidence: int

def run_chat(client, model):
    print(f"\n--- Testing model: {model} ---")
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Please output valid JSON matching the schema: {\"message\": \"str\", \"confidence\": \"int\"}."
                },
                {
                    "role": "user",
                    "content": "Say hello to FinPay Audit team."
                }
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        content = completion.choices[0].message.content
        print(f"Raw response:\n{content}")
        
        # Pydantic validation
        parsed = ExampleSchema.model_validate_json(content)
        print(f"Parsed and validated: {parsed}")
        
    except Exception as e:
        print(f"Error testing model {model}: {e}")

def main():
    if not API_KEY or API_KEY == "your_groq_api_key":
        print("Please set GROQ_API_KEY in .env")
        return

    print("Initializing Groq client...")
    client = Groq(api_key=API_KEY)
    
    print("Listing models...")
    try:
        models = client.models.list()
        model_ids = [m.id for m in models.data]
        print(f"Found {len(model_ids)} models.")
        
        if PRIMARY_MODEL in model_ids:
            print(f"✅ Primary model '{PRIMARY_MODEL}' is available.")
        else:
            print(f"❌ Primary model '{PRIMARY_MODEL}' is NOT found in models list.")
            
        if FALLBACK_MODEL in model_ids:
            print(f"✅ Fallback model '{FALLBACK_MODEL}' is available.")
        else:
            print(f"❌ Fallback model '{FALLBACK_MODEL}' is NOT found in models list.")
            
    except Exception as e:
        print(f"Error listing models: {e}")

    run_chat(client, PRIMARY_MODEL)
    run_chat(client, FALLBACK_MODEL)

if __name__ == "__main__":
    main()
