import os
import sys
import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Ensure the backend directory is in the sys.path so we can import from agent etc.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "ok" in data
    assert data["ok"] is True
    assert "hindsight" in data
    assert "llm" in data

def test_readiness():
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "flags" in data
    assert isinstance(data["score"], int)

def test_ask_no_memory():
    response = client.post("/ask", json={"question": "What is the status of backups?", "use_memory": False})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["used_memory"] is False
    assert "sources" in data
    assert "memories" in data

def test_ask_with_memory():
    response = client.post("/ask", json={"question": "Are there any backup issues?", "use_memory": True})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["used_memory"] is True
    assert "sources" in data
    assert "memories" in data

def test_feedback_success():
    readiness_res = client.get("/readiness")
    flags = readiness_res.json().get("flags", [])
    if not flags:
        pytest.skip("No flags found to test feedback")
        
    flag_id = flags[0]["id"]
    response = client.post("/feedback", json={"flag_id": flag_id, "action": "resolved", "evidence_ref": "EV-123"})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "new_score" in data
    assert "explanation" in data

def test_feedback_error_missing_evidence():
    response = client.post("/feedback", json={"flag_id": "dummy:ID", "action": "resolved"})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data

def test_feedback_error_not_found():
    response = client.post("/feedback", json={"flag_id": "nonexistent:ID", "action": "resolved", "evidence_ref": "EV-123"})
    assert response.status_code == 404
    data = response.json()
    assert "error" in data

def test_demo_reset():
    response = client.post("/demo/reset")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
