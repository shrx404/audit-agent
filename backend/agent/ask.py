from typing import List, Dict, Any, Tuple
from schemas import Flag, MemoryHit
from agent.llm import AgentLLM
from agent.prompts import ASK_SYSTEM_PROMPT
from memory.client import HindsightWrapper
from pydantic import BaseModel

class AskResponseFormat(BaseModel):
    answer: str
    sources: List[str]

def ask_agent(question: str, use_memory: bool, open_flags: List[Flag], hindsight: HindsightWrapper, llm: AgentLLM) -> Tuple[str, List[str], List[MemoryHit]]:
    if not use_memory:
        user_prompt = f"Question: {question}\n\nNote: You have NO access to company history. Provide generic advice."
        try:
            res = llm.generate_json(ASK_SYSTEM_PROMPT, user_prompt, AskResponseFormat)
            return res.answer, [], []
        except Exception:
            return "I cannot answer that right now.", [], []
            
    # use_memory = True
    memories = hindsight.recall(question)
    memory_texts = "\n".join([f"- [{m.id}] {m.text}" for m in memories[:10]])
    
    flags_text = "\n".join([f"- {f.id}: {f.explanation}" for f in open_flags])
    
    user_prompt = f"""Question: {question}

Current Open Flags:
{flags_text}

Recalled History:
{memory_texts}
"""
    try:
        res = llm.generate_json(ASK_SYSTEM_PROMPT, user_prompt, AskResponseFormat)
        valid_sources = [s for s in res.sources if s in memory_texts or any(s in f.id for f in open_flags) or s in question]
        if not valid_sources:
            return "No supporting history found.", [], memories
            
        return res.answer, valid_sources, memories
    except Exception as e:
        return f"Error analyzing history: {str(e)}", [], []
