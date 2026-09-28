import os
import pytest
import httpx
from unittest.mock import patch, MagicMock

# Fix import path for pytest running in backend/
from services.llm_client import LLMClient, LLMClientError

@patch.dict(os.environ, {"OMNIROUTE_API_KEY": "test-omni", "OMNIROUTE_BASE_URL": "http://test", "OMNIROUTE_MODEL": "test-model"})
def test_llm_client_omniroute_init():
    client = LLMClient()
    assert client.is_omniroute is True
    assert client.model == "test-model"

@patch.dict(os.environ, {"GROQ_API_KEY": "test-groq", "OMNIROUTE_API_KEY": ""})
def test_llm_client_groq_fallback():
    client = LLMClient()
    assert client.is_omniroute is False
    assert client.model == "openai/gpt-oss-120b"
    
@patch.dict(os.environ, {"OMNIROUTE_API_KEY": "test-omni", "OMNIROUTE_BASE_URL": "http://test", "OMNIROUTE_MODEL": "test-model"})
@patch("services.llm_client.httpx.Client")
def test_chat_completion_omniroute_success(mock_httpx_client_class):
    mock_instance = MagicMock()
    mock_httpx_client_class.return_value.__enter__.return_value = mock_instance
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "test response"}}]
    }
    mock_instance.post.return_value = mock_response
    
    client = LLMClient()
    result = client.chat_completion([{"role": "user", "content": "hi"}])
    
    assert result == "test response"
    # Ensure timeout=60.0 is used
    mock_httpx_client_class.assert_called_once_with(timeout=60.0)
    mock_instance.post.assert_called_once_with(
        "http://test/chat/completions",
        json={"model": "test-model", "messages": [{"role": "user", "content": "hi"}]},
        headers={"Authorization": "Bearer test-omni", "Content-Type": "application/json"}
    )

@patch.dict(os.environ, {"OMNIROUTE_API_KEY": "test-omni", "OMNIROUTE_BASE_URL": "http://test/", "OMNIROUTE_MODEL": "test-model"})
@patch("services.llm_client.httpx.Client")
def test_chat_completion_trailing_slash(mock_httpx_client_class):
    mock_instance = MagicMock()
    mock_httpx_client_class.return_value.__enter__.return_value = mock_instance
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "test response"}}]
    }
    mock_instance.post.return_value = mock_response
    
    client = LLMClient()
    client.chat_completion([{"role": "user", "content": "hi"}])
    
    # Assert URL is normalized
    args, kwargs = mock_instance.post.call_args
    assert args[0] == "http://test/chat/completions"

@patch.dict(os.environ, {"OMNIROUTE_API_KEY": "test-omni", "OMNIROUTE_BASE_URL": "http://test", "OMNIROUTE_MODEL": "test-model"})
@patch("services.llm_client.httpx.Client")
def test_chat_completion_http_status_error(mock_httpx_client_class):
    mock_instance = MagicMock()
    mock_httpx_client_class.return_value.__enter__.return_value = mock_instance
    
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server error", request=MagicMock(), response=mock_response
    )
    mock_instance.post.return_value = mock_response
    
    client = LLMClient()
    with pytest.raises(LLMClientError, match="HTTP status: 500"):
        client.chat_completion([{"role": "user", "content": "hi"}])

@patch.dict(os.environ, {"OMNIROUTE_API_KEY": "test-omni", "OMNIROUTE_BASE_URL": "http://test", "OMNIROUTE_MODEL": "test-model"})
@patch("services.llm_client.httpx.Client")
def test_chat_completion_request_error(mock_httpx_client_class):
    mock_instance = MagicMock()
    mock_httpx_client_class.return_value.__enter__.return_value = mock_instance
    
    mock_instance.post.side_effect = httpx.RequestError("Timeout", request=MagicMock())
    
    client = LLMClient()
    with pytest.raises(LLMClientError, match="connection or timeout error"):
        client.chat_completion([{"role": "user", "content": "hi"}])
        
@patch.dict(os.environ, {"GROQ_API_KEY": "test-groq", "OMNIROUTE_API_KEY": ""})
@patch("services.llm_client.Groq")
def test_chat_completion_groq(mock_groq_class):
    mock_instance = MagicMock()
    mock_groq_class.return_value = mock_instance
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "groq test response"
    mock_instance.chat.completions.create.return_value = mock_response
    
    client = LLMClient()
    result = client.chat_completion([{"role": "user", "content": "hi"}])
    
    assert result == "groq test response"
    mock_instance.chat.completions.create.assert_called_once_with(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "hi"}]
    )
