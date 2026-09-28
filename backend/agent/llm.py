import os
import time
import json
import logging
from typing import TypeVar, Type, Any
from pydantic import BaseModel
from groq import Groq

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class LLMError(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code

class AgentLLM:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY missing in environment variables.")
        
        self.primary_model = os.environ.get("LLM_PRIMARY_MODEL", "openai/gpt-oss-120b")
        self.fallback_model = os.environ.get("LLM_FALLBACK_MODEL", "qwen/qwen3.8-27b")
        self.client = Groq(api_key=self.api_key, timeout=30.0)

    def _call_groq(self, model: str, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Groq specific retry logic
        attempts = 3
        for attempt in range(attempts):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                return response.choices[0].message.content
            except Exception as e:
                status_code = getattr(e, 'status_code', None)
                if status_code in (429, 500, 502, 503, 504) or attempt < attempts - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise LLMError(f"Groq API failed: {str(e)}", "llm_failed")

    def _parse_json(self, content: str) -> dict:
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())

    def generate_json(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        try:
            content = self._call_groq(self.primary_model, system_prompt, user_prompt)
            data = self._parse_json(content)
            return response_model.model_validate(data)
        except Exception as e:
            logger.warning(f"Primary model failed: {str(e)}. Retrying with 'valid JSON only'...")
            
            # Retry once with primary model asking for valid JSON
            try:
                content = self._call_groq(self.primary_model, system_prompt, user_prompt + "\n\nReturn ONLY valid JSON.")
                data = self._parse_json(content)
                return response_model.model_validate(data)
            except Exception as e2:
                logger.warning(f"Primary model retry failed: {str(e2)}. Falling back to {self.fallback_model}...")
                
                # Fallback model
                try:
                    content = self._call_groq(self.fallback_model, system_prompt, user_prompt)
                    data = self._parse_json(content)
                    return response_model.model_validate(data)
                except Exception as e3:
                    logger.error(f"Fallback model failed: {str(e3)}")
                    raise LLMError("LLM failed to produce valid output", "llm_failed")
