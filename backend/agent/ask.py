import logging
from typing import List, Dict, Any, Tuple, Optional
from schemas import Flag, MemoryHit
from agent.llm import AgentLLM
from agent.prompts import ASK_SYSTEM_PROMPT
from memory.client import HindsightWrapper
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class AskResponseFormat(BaseModel):
    answer: str
    records: Optional[str] = None
    recurrence: Optional[str] = None
    evidence_gaps: Optional[str] = None
    prediction: Optional[str] = None
    limitations: Optional[str] = None
    sources: List[str]

def ask_agent(question: str, use_memory: bool, open_flags: List[Flag], hindsight: HindsightWrapper, llm: AgentLLM) -> Tuple[str, List[str], List[MemoryHit]]:
    if not use_memory:
        user_prompt = f"Question: {question}\n\nNote: You have NO access to company history. Provide generic advice."
        try:
            res = llm.generate_json(ASK_SYSTEM_PROMPT, user_prompt, AskResponseFormat)
            final_answer = res.answer
            return final_answer, [], []
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
    
    # Log memory context
    logger.info(f"Dataset ID: {hindsight.bank_id}")
    logger.info(f"Final Prompt:\n{user_prompt}")
    for m in memories:
        logger.info(f"Retrieved Memory - ID: {m.id}, Text: {m.text}")
        
    try:
        res = llm.generate_json(ASK_SYSTEM_PROMPT, user_prompt, AskResponseFormat)
        logger.info(f"LLM Response: {res.model_dump_json()}")
        
        valid_sources = []
        for s in res.sources:
            s_clean = s.replace("\u2011", "-").replace("source", "").strip(" ()[]")
            for m in memories:
                m_text = m.text.replace("\u2011", "-")
                if s_clean in m.id or m.id in s_clean or (len(s_clean) >= 4 and s_clean.lower() in m_text.lower()):
                    if m.id not in valid_sources:
                        valid_sources.append(m.id)
            for f in open_flags:
                f_text = f.explanation.replace("\u2011", "-")
                if (
                    s_clean in f.id
                    or f.id in s_clean
                    or s_clean in f.control_id
                    or any(s_clean in src for src in f.sources)
                    or (len(s_clean) >= 4 and s_clean.lower() in f_text.lower())
                ):
                    if f.id not in valid_sources:
                        valid_sources.append(f.id)
                        
        if not valid_sources and len(res.sources) > 0:
            return "I cannot answer this question because there is insufficient evidence in the provided history.", [], memories
            
        if not valid_sources and "No supporting history" not in res.answer:
            if memories:
                # Should not use a random valid_source if none matched!
                return "I cannot answer this question because there is insufficient evidence in the provided history.", [], memories
            else:
                return "No supporting history found.", [], memories
                
        final_answer = res.answer
        if res.records:
            final_answer += f"\n\n### Records\n{res.records}"
        if res.recurrence:
            final_answer += f"\n\n### Recurrence\n{res.recurrence}"
        if res.evidence_gaps:
            final_answer += f"\n\n### Evidence Gaps\n{res.evidence_gaps}"
        if res.prediction:
            final_answer += f"\n\n### Prediction\n{res.prediction}"
        if res.limitations:
            final_answer += f"\n\n### Limitations\n{res.limitations}"
            
        return final_answer, valid_sources, memories
    except Exception as e:
        return f"Error analyzing history: {str(e)}", [], []
