import os
import sys
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ai_engine import call_ai_model

@patch("requests.post")
def test_ai_provider_routing(mock_post):
    # Setup mock response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": '{"fit": "good"}'}}], # for openai/grok/groq
        "candidates": [{"content": {"parts": [{"text": '{"fit": "good"}'}]}}], # for gemini
        "content": [{"text": '{"fit": "good"}'}] # for claude
    }
    mock_post.return_value = mock_resp

    print("--- Testing AI Provider Routing Mock Tests ---")
    
    # 1. Google Gemini
    res = call_ai_model("test prompt", "gemini", "gemini-1.5-flash", "test-key")
    print(f"Gemini route returns: {res}")
    mock_post.assert_called_with(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=test-key",
        json={"contents": [{"parts": [{"text": "test prompt"}]}], "generationConfig": {"responseMimeType": "application/json"}},
        headers={"Content-Type": "application/json"},
        timeout=60
    )
    
    # 2. OpenAI ChatGPT
    res = call_ai_model("test prompt", "openai", "gpt-4o-mini", "test-key")
    print(f"OpenAI route returns: {res}")
    mock_post.assert_called_with(
        "https://api.openai.com/v1/chat/completions",
        json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "test prompt"}], "temperature": 0.7, "response_format": {"type": "json_object"}},
        headers={"Content-Type": "application/json", "Authorization": "Bearer test-key"},
        timeout=60
    )

    # 3. ChatGPTX (alias for OpenAI)
    res = call_ai_model("test prompt", "chatgptx", "gpt-4o", "test-key")
    print(f"ChatGPTX route returns: {res}")
    mock_post.assert_called_with(
        "https://api.openai.com/v1/chat/completions",
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": "test prompt"}], "temperature": 0.7, "response_format": {"type": "json_object"}},
        headers={"Content-Type": "application/json", "Authorization": "Bearer test-key"},
        timeout=60
    )

    # 4. Anthropic Claude
    res = call_ai_model("test prompt", "claude", "claude-3-5-sonnet-20241022", "test-key")
    print(f"Claude route returns: {res}")
    mock_post.assert_called_with(
        "https://api.anthropic.com/v1/messages",
        json={"model": "claude-3-5-sonnet-20241022", "max_tokens": 4096, "messages": [{"role": "user", "content": "test prompt"}]},
        headers={"x-api-key": "test-key", "anthropic-version": "2023-06-01", "content-type": "application/json"},
        timeout=60
    )

    # 5. Gorx (alias for Grok / xAI)
    res = call_ai_model("test prompt", "gorx", "grok-beta", "test-key")
    print(f"Gorx (Grok) route returns: {res}")
    mock_post.assert_called_with(
        "https://api.x.ai/v1/chat/completions",
        json={"model": "grok-beta", "messages": [{"role": "user", "content": "test prompt"}], "temperature": 0.7, "response_format": {"type": "json_object"}},
        headers={"Content-Type": "application/json", "Authorization": "Bearer test-key"},
        timeout=60
    )

    # 6. Groq
    res = call_ai_model("test prompt", "groq", "llama3-8b-8192", "test-key")
    print(f"Groq route returns: {res}")
    mock_post.assert_called_with(
        "https://api.groq.com/openai/v1/chat/completions",
        json={"model": "llama3-8b-8192", "messages": [{"role": "user", "content": "test prompt"}], "temperature": 0.7, "response_format": {"type": "json_object"}},
        headers={"Content-Type": "application/json", "Authorization": "Bearer test-key"},
        timeout=60
    )

    print("\nSUCCESS: All AI Provider API routing tests passed!")

if __name__ == "__main__":
    test_ai_provider_routing()
