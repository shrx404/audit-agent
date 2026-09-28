from typing import List, Tuple, Dict, Any
from schemas import Flag

def calculate_score(flags: List[Flag]) -> Tuple[int, List[Dict[str, Any]]]:
    kind_weights = {
        "repeat_finding": 15,
        "done_no_evidence": 12,
        "stale_ticket": 8,
        "overdue_test": 6
    }
    
    severity_multipliers = {
        "high": 1.0,
        "medium": 0.7,
        "low": 0.4
    }
    
    score = 100.0
    breakdown = []
    
    for flag in flags:
        if flag.state != "open":
            continue
            
        weight = kind_weights.get(flag.kind, 0)
        multiplier = severity_multipliers.get(flag.severity, 0.0)
        penalty = weight * multiplier
        
        score -= penalty
        breakdown.append({
            "flag_id": flag.id,
            "points": -round(penalty)
        })
        
    final_score = max(0, min(100, round(score)))
    return final_score, breakdown
