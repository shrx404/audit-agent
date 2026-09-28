import os
import httpx
from typing import List, Dict, Optional
from groq import Groq

class LLMClientError(Exception):
    """Custom exception for LLM Client operations."""
    pass

class LLMClient:
    def __init__(self):
        omniroute_key = os.getenv("OMNIROUTE_API_KEY")
        omniroute_base = os.getenv("OMNIROUTE_BASE_URL")
        
        # Default OMNIROUTE_MODEL to groq/openai/gpt-oss-120b if absent
        self.model = os.getenv("OMNIROUTE_MODEL", "groq/openai/gpt-oss-120b")
        
        # Keep existing direct Groq configuration available as fallback
        groq_key = os.getenv("GROQ_API_KEY")
        
        if omniroute_key and omniroute_base:
            self.omniroute_key = omniroute_key
            self.omniroute_base = omniroute_base
            self.is_omniroute = True
        elif groq_key:
            self.client = Groq(api_key=groq_key)
            self.is_omniroute = False
            self.model = os.getenv("LLM_PRIMARY_MODEL", "openai/gpt-oss-120b")
        else:
            raise ValueError("Neither OMNIROUTE_API_KEY nor GROQ_API_KEY is configured.")

    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Perform a chat completion using the configured client and model.
        """
        if self.is_omniroute:
            payload = {
                "model": self.model,
                "messages": messages,
            }
            if response_format:
                payload["response_format"] = response_format
                
            headers = {
                "Authorization": f"Bearer {self.omniroute_key}",
                "Content-Type": "application/json"
            }
            
            # Make sure URL is normalized to avoid trailing slash issues
            url = f"{self.omniroute_base.rstrip('/')}/chat/completions"
            
            try:
                # Use a 60 second timeout for potentially slow LLM completions
                with httpx.Client(timeout=60.0) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    resp.raise_for_status()
                    return resp.json()["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                # Handle status errors (4xx, 5xx) returning clean error message
                status = e.response.status_code
                raise LLMClientError(f"LLM request failed with HTTP status: {status}") from e
            except httpx.RequestError as e:
                # Handle connection errors, timeouts
                raise LLMClientError("LLM request encountered a connection or timeout error.") from e
        else:
            kwargs = {
                "model": self.model,
                "messages": messages,
            }
            if response_format:
                kwargs["response_format"] = response_format
                
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
