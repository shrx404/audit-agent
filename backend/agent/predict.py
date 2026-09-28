from typing import List, Dict, Any, Optional
from schemas import Flag, Prediction, MemoryHit
from agent.llm import AgentLLM
from agent.prompts import PREDICT_SYSTEM_PROMPT
from memory.client import HindsightWrapper

def generate_predictions(flags: List[Flag], hindsight: HindsightWrapper, llm: AgentLLM) -> List[Prediction]:
    predictions = []
    
    # One reflect call for cross-year patterns
    reflect_text = hindsight.reflect("What findings tend to recur and why?")
    
    for flag in flags:
        if flag.state != "open":
            continue
            
        # Recall related history
        # For repeat finding and overdue test, search for the control id
        query = f"history of control {flag.control_id}"
        memories = hindsight.recall(query)
        
        # Attach memories to flag
        flag.memories = memories
        
        memory_texts = "\n".join([f"- [{m.id}] {m.text}" for m in memories[:10]])
        
        user_prompt = f"""Control: {flag.control_id}
Flag Kind: {flag.kind}
Flag Explanation: {flag.explanation}

Cross-Year Patterns (Reflect):
{reflect_text}

Recalled Memories for {flag.control_id}:
{memory_texts}
"""
        try:
            pred = llm.generate_json(PREDICT_SYSTEM_PROMPT, user_prompt, Prediction)
            
            # Verify sources exist in the index (memories or flag sources)
            # In a real app we'd check against a full record index, but here we can check against memories
            valid_sources = [s for s in pred.sources if s in memory_texts or s in flag.sources]
            if valid_sources:
                pred.sources = valid_sources
                predictions.append(pred)
        except Exception as e:
            # Drop prediction on failure or empty valid sources
            print(f"Failed to generate prediction for {flag.control_id}: {e}")
            
    return predictions
