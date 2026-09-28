import os
from dotenv import load_dotenv

# Load env variables before importing agent components
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from agent.core import get_readiness_report
from agent.state import save_feedback, reset_feedback, load_feedback
from agent.ask import ask_agent
from agent.cache import clear_cache
from memory.client import HindsightWrapper
from agent.llm import AgentLLM
from schemas import MemoryHit

app = FastAPI(title="AuditMemory API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("NEXT_PUBLIC_API_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    code = getattr(exc, "code", "internal_error")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "code": code}
    )

@app.get("/health")
def health_check():
    # Basic check
    try:
        hw = HindsightWrapper()
        hindsight_ok = True
    except Exception:
        hindsight_ok = False
        
    try:
        llm = AgentLLM()
        llm_ok = True
    except Exception:
        llm_ok = False
        
    return {"ok": True, "hindsight": hindsight_ok, "llm": llm_ok}

@app.get("/readiness")
def readiness():
    return get_readiness_report()

class AskRequest(BaseModel):
    question: str
    use_memory: bool

@app.post("/ask")
def ask(req: AskRequest):
    hindsight = HindsightWrapper()
    llm = AgentLLM()
    report = get_readiness_report()
    open_flags = [f for f in report.flags if f.state == "open"]
    
    answer, sources, memories = ask_agent(req.question, req.use_memory, open_flags, hindsight, llm)
    return {
        "answer": answer,
        "sources": sources,
        "memories": memories,
        "used_memory": req.use_memory
    }

class FeedbackRequest(BaseModel):
    flag_id: str
    action: str
    evidence_ref: Optional[str] = None
    note: Optional[str] = None

@app.post("/feedback")
def feedback(req: FeedbackRequest):
    if req.action == "resolved" and not req.evidence_ref:
        return JSONResponse(status_code=400, content={"error": "Resolved action requires evidence_ref", "code": "bad_request"})
        
    report_before = get_readiness_report()
    flag = next((f for f in report_before.flags if f.id == req.flag_id), None)
    if not flag:
        return JSONResponse(status_code=404, content={"error": "Flag not found", "code": "not_found"})
        
    # Apply feedback
    current_feedback = load_feedback()
    current_feedback[req.flag_id] = {
        "action": req.action,
        "evidence_ref": req.evidence_ref,
        "note": req.note
    }
    save_feedback(current_feedback)
    
    report_after = get_readiness_report()
    score_diff = report_after.score - report_before.score
    diff_str = f"+{score_diff}" if score_diff >= 0 else str(score_diff)
    
    if req.action == "resolved":
        explanation = f"Closed with evidence {req.evidence_ref}. Score {report_before.score} to {report_after.score} ({diff_str})."
    elif req.action == "false_alarm":
        explanation = f"Marked as false alarm. Score {report_before.score} to {report_after.score} ({diff_str})."
    else:
        explanation = f"Marked as still open. Score {report_before.score} to {report_after.score} ({diff_str})."
        
    return {
        "ok": True,
        "new_score": report_after.score,
        "explanation": explanation
    }

@app.post("/demo/reset")
def demo_reset():
    reset_feedback()
    return {"ok": True}
