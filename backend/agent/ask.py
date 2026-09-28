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
        valid_sources = []
        for s in res.sources:
            s_clean = s.replace("source", "").strip(" ()[]")
            for m in memories:
                if s_clean in m.id or m.id in s_clean or (len(s_clean) >= 6 and s_clean in m.id):
                    if m.id not in valid_sources:
                        valid_sources.append(m.id)
            for f in open_flags:
                if s_clean in f.id or f.id in s_clean or (len(s_clean) >= 6 and s_clean in f.id):
                    if f.id not in valid_sources:
                        valid_sources.append(f.id)
                        
        if not valid_sources and "No supporting history" not in res.answer:
            return "No supporting history found.", [], memories
            
        return res.answer, valid_sources, memories
    except Exception as e:
        return f"Error analyzing history: {str(e)}", [], []
