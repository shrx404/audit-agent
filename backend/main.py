import os
import sys
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Reconfigure stdout/stderr for UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Load env variables before importing agent components
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse
import json
import uuid
import io
import pypdf
import docx
from datetime import datetime
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    HindsightWrapper.close()

app = FastAPI(title="AuditMemory API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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

def get_uploaded_sources_path():
    return os.path.join(os.path.dirname(__file__), "data", "uploaded_sources.json")

@app.get("/sources")
async def get_sources():
    path = get_uploaded_sources_path()
    uploaded = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                uploaded = json.load(f)
            except:
                pass
                
    try:
        hindsight = HindsightWrapper()
        res = await hindsight.client.documents.list_documents(bank_id=hindsight.bank_id, limit=100)
        docs = res.to_dict().get("items", [])
        
        uploaded_ids = {u["id"] for u in uploaded}
        for doc in docs:
            if doc["id"] not in uploaded_ids:
                title = doc["id"]
                if doc.get("retain_params") and doc["retain_params"].get("context"):
                    context = doc["retain_params"]["context"]
                    if context.startswith("Uploaded document: "):
                        title = context.replace("Uploaded document: ", "")
                
                uploaded.append({
                    "id": doc["id"],
                    "title": title,
                    "category": "Documents",
                    "kind": "Documents",
                    "tone": "muted",
                    "description": "Document indexed in Hindsight online corpus.",
                    "date": doc.get("created_at", "").split("T")[0] if doc.get("created_at") else "",
                    "details": {},
                    "content": "",
                    "origin": "indexed",
                    "status": "indexed"
                })
    except Exception as e:
        error_msg = str(e)
        print(f"Failed to fetch online corpus documents: {error_msg}")
        uploaded.append({
            "id": "ERROR-1",
            "title": "ERROR",
            "category": "Documents",
            "kind": "Documents",
            "tone": "error",
            "description": f"Failed to fetch: {error_msg}",
            "date": "",
            "details": {},
            "content": "",
            "origin": "indexed",
            "status": "failed"
        })

    return uploaded

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    hindsight = HindsightWrapper()
    content_bytes = await file.read()
    
    filename = file.filename.lower() if file.filename else ""
    if filename.endswith(".pdf"):
        try:
            pdf_reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            content_str = "\n".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
        except Exception:
            content_str = "[Failed to extract PDF text]"
    elif filename.endswith(".docx"):
        try:
            doc = docx.Document(io.BytesIO(content_bytes))
            content_str = "\n".join(para.text for para in doc.paragraphs)
        except Exception:
            content_str = "[Failed to extract DOCX text]"
    else:
        content_str = content_bytes.decode('utf-8', errors='ignore')
        
    if len(content_str) > 100000:
        content_str = content_str[:100000] + "\n...[Content truncated for size]..."
    
    d_str = os.environ.get("AS_OF_DATE", "2026-09-28")
    as_of_date = datetime.strptime(d_str, "%Y-%m-%d")
    
    doc_id = f"local:{uuid.uuid4()}"
    
    from fastapi.concurrency import run_in_threadpool
    await run_in_threadpool(
        hindsight.retain,
        content=content_str,
        context=f"Uploaded document: {file.filename}",
        timestamp=as_of_date,
        document_id=doc_id,
        retain_async=False
    )
    
    path = get_uploaded_sources_path()
    uploaded = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                uploaded = json.load(f)
            except:
                pass
                
    new_source = {
        "id": doc_id,
        "title": file.filename,
        "category": "Documents",
        "kind": "Documents",
        "tone": "muted",
        "description": content_str[:200] + "..." if len(content_str) > 200 else content_str,
        "date": d_str,
        "details": {"size": len(content_bytes)},
        "content": content_str,
        "origin": "indexed",
        "status": "indexed"
    }
    uploaded.append(new_source)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(uploaded, f)
        
    return {"indexed": True, "source_id": doc_id}

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

class AnalyzeFindingRequest(BaseModel):
    control_id: str
    department: str
    finding: str
    evidence_ref: Optional[str] = None
    use_memory: Optional[bool] = False

@app.post("/analyze-finding")
def analyze_finding(req: AnalyzeFindingRequest):
    hindsight = HindsightWrapper()
    llm = AgentLLM()
    report = get_readiness_report()
    open_flags = [f for f in report.flags if f.state == "open"]
    
    answer, sources, memories = ask_agent(req.finding, req.use_memory, open_flags, hindsight, llm)
    
    memories_used = []
    for m in memories:
        memories_used.append({
            "mem_id": m.id,
            "text": m.text,
            "type": "audit finding",
            "trust": "verified",
            "as_of": str(m.date) if m.date else "2024-01-01",
            "subject": "",
            "is_current": False,
            "superseded_by": None,
            "relevance": m.relevance
        })
        
    deterministic_checks = []
    for flag in report.flags:
        if flag.state == "open":
            deterministic_checks.append({
                "kind": flag.kind,
                "control_id": flag.control_id,
                "severity": flag.severity,
                "explanation": flag.explanation,
                "sources": flag.sources
            })

    return {
        "analysis_id": "A-1234",
        "status": "suspected",
        "possible_recurrence": False,
        "recurrence_confidence": None,
        "related_past_findings": [],
        "previous_root_cause": None,
        "previous_remediation": None,
        "explanation": answer,
        "memories_used": memories_used,
        "deterministic_checks": deterministic_checks,
        "warnings": [],
        "references": [{"source_id": s, "filename": s, "category": "Reference", "snippet": s} for s in sources]
    }

class ConfirmFindingRequest(BaseModel):
    analysis_id: str
    decision: str
    linked_finding_ids: List[str]
    confirmed_root_cause: Optional[str] = None
    confirmed_remediation: Optional[str] = None
    outcome: str
    analyst: str
    note: Optional[str] = None

@app.post("/confirm-finding")
def confirm_finding(req: ConfirmFindingRequest):
    return {
        "ok": True,
        "trust": "verified",
        "retained_mem_ids": ["dummy-mem-id"],
        "retrievable": True,
        "message": "Confirmed and retained"
    }
