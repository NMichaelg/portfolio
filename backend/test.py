
# Portfolio/backend/tests/test_resume_tools.py
import os
from dotenv import load_dotenv
import asyncio
import json

from pathlib import Path
from pprint import pprint
from langchain.messages import HumanMessage
from langchain_openai import ChatOpenAI

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from auth import (
    check_password,
    is_authorized,
    validate_byok,
    require_access,
    _attempts,
    _authorized_threads,
)
MAX_ATTEMPTS = 5
from agents import read_and_format_resume
from agents import get_github_repos, get_repo_details
from agents import graph
from agents import get_llm, DEFAULT_LLM
from streaming import stream_chat_response
from main import app



load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RESUME_PATH = PROJECT_ROOT / "local_info" / "resume-no-password.md"

def test_read_and_format_resume_splits_markdown():

    docs = read_and_format_resume(str(RESUME_PATH))

    assert any(doc.page_content.strip() for doc in docs)
    assert len(docs) > 0


def test_search_resume_tool():
    from agents import search_resume

    query = "What does the candidate know any other language beside English?"
    result = search_resume.invoke({"query": query})

def test_get_github_repos():
    repos = get_github_repos.invoke({})
    assert isinstance(repos, list)
    assert len(repos) > 0

def test_repo_details():
    repo_name = "portfolio"
    details = get_repo_details.invoke({"repo_name": repo_name})
    assert details.name == repo_name
    assert details.readme_excerpt is not None

def test_graph():
    messages = [HumanMessage(content = "Who are you")]
    config = {"thread_id" : "test_thread1"}
    response = graph.invoke(
        {"messages" : messages},
        {"configurable" : config}
    )
    for m in response["messages"] :
        m.pretty_print()


def test_draw_graph():
    png_bytes = graph.get_graph().draw_mermaid_png()

    with open("graph.png", "wb") as f:
        f.write(png_bytes)

## API level test
class _FakeRequest:
    """Minimal stand-in for fastapi.Request -- just enough for auth._client_id."""
 
    def __init__(self, ip="127.0.0.1"):
        self.headers = {"x-forwarded-for": ip}
        self.client = MagicMock(host=ip)

@pytest.fixture(autouse=True)
def reset_auth_state():
    """auth.py's lockout/authorization state is module-level and shared
    across the whole test session -- reset it before and after each test
    so tests don't leak into each other (same idea as the GitHub cache
    reset fixture)."""
    _attempts.clear()
    _authorized_threads.clear()
    yield
    _attempts.clear()
    _authorized_threads.clear()

def test_check_password_correct_authorizes_thread():
    req = _FakeRequest()
    check_password(req, "thread-a", os.environ["CHAT_PASSWORD"])
    assert is_authorized("thread-a") is True

def test_check_password_wrong_raises_401_and_does_not_authorize():
    req = _FakeRequest()
    with pytest.raises(HTTPException) as exc_info:
        check_password(req, "thread-b", "definitely-wrong")
    assert exc_info.value.status_code == 401
    assert is_authorized("thread-b") is False

def test_check_password_locks_out_after_max_attempts():
    req = _FakeRequest(ip="1.2.3.4")
 
    for _ in range(MAX_ATTEMPTS-1):
        with pytest.raises(HTTPException) as exc_info:
            check_password(req, "thread-c", "wrong")
        assert exc_info.value.status_code == 401
 
    # The MAX_ATTEMPTS-th wrong attempt should lock out (429), not 401.
    with pytest.raises(HTTPException) as exc_info:
        check_password(req, "thread-c", "wrong")
    assert exc_info.value.status_code == 429
 
    # Even the correct password is rejected while locked out.
    with pytest.raises(HTTPException) as exc_info:
        check_password(req, "thread-c", os.environ["CHAT_PASSWORD"])
    assert exc_info.value.status_code == 429

def test_check_password_lockout_is_per_ip(): 
    req_a = _FakeRequest(ip="1.1.1.1")
    req_b = _FakeRequest(ip="2.2.2.2")
 
    for _ in range(MAX_ATTEMPTS):
        with pytest.raises(HTTPException):
            check_password(req_a, "thread-d", "wrong")
 
    # A different IP isn't affected by req_a's lockout.
    check_password(req_b, "thread-e", os.environ["CHAT_PASSWORD"])
    assert is_authorized("thread-e") is True

@pytest.mark.parametrize(
    "provider,api_key",
    [
        ("openai", "sk-" + "a" * 20),
        ("anthropic", "sk-ant-" + "a" * 20),
        ("gemini", "AIza" + "a" * 20),
    ],
)
def test_validate_byok_accepts_well_formed_keys(provider, api_key):
    validate_byok(provider, api_key)  # should not raise

@pytest.mark.parametrize(
    "provider,api_key",
    [
        (None, None),
        ("openai", None),
        (None, "sk-" + "a" * 20),
        ("made_up_provider", "sk-" + "a" * 20),
        ("openai", "not-a-real-key"),
        ("anthropic", "sk-" + "a" * 20),  # missing the "ant-" segment
    ],
)
def test_validate_byok_rejects_bad_input(provider, api_key):
    with pytest.raises(HTTPException):
        validate_byok(provider, api_key)

def test_require_access_passes_for_password_authorized_thread():
    req = _FakeRequest()
    check_password(req, "thread-f", os.environ["CHAT_PASSWORD"])
    require_access(req, "thread-f", provider=None, api_key=None)  # should not raise


def test_require_access_rejects_unauthorized_thread_without_byok():

    req = _FakeRequest()
    with pytest.raises(HTTPException) as exc_info:
        require_access(req, "thread-g", provider=None, api_key=None)
    assert exc_info.value.status_code == 401

#  BYOK routing

def test_get_llm_falls_back_to_default_with_no_byok_fields():
    result = get_llm({"configurable": {"thread_id": "x"}})
    assert result is DEFAULT_LLM

def test_get_llm_falls_back_to_default_with_no_config():
    assert get_llm(None) is DEFAULT_LLM

def test_get_llm_builds_a_client_for_byok():
    config = {"configurable": {"provider": "google", "api_key": os.environ["TESTING_ONLY_LLM_API_KEY"]}}
    byok_llm = get_llm(config)
    assert byok_llm is not DEFAULT_LLM
    assert isinstance(byok_llm, ChatOpenAI)

def test_get_llm_never_caches_byok_clients():
    config = {"configurable": {"provider": "google", "api_key": os.environ["TESTING_ONLY_LLM_API_KEY"]}}
    first = get_llm(config)
    second = get_llm(config)
    assert first is not second

# NDJSON streaming

class _FakeChunk:
    def __init__(self, content):
        self.content = content
 
 
class _FakeToolOutput:
    def __init__(self, content):
        self.content = content
 
 
class _FakeStateSnapshot:
    next = ()
    tasks = []

async def _fake_astream_events(input_state, config, version="v2"):

    """
    Simulates one turn: classify_intent's structured-output tokens
    (should be filtered out), qa_agent's real answer tokens (should pass
    through), a mapped tool finishing (navigate_to_section), and an
    unmapped tool finishing (search_resume -- should be skipped, since
    its output only feeds the LLM and was never meant to be shown raw).
    """
    events = [
        {
            "event": "on_chat_model_stream",
            "metadata": {"langgraph_node": "classify_intent"},
            "data": {"chunk": _FakeChunk('{"route":"qa"}')},
        },
        {
            "event": "on_chat_model_stream",
            "metadata": {"langgraph_node": "qa_agent"},
            "data": {"chunk": _FakeChunk("Hello!")},
        },
        {
            "event": "on_tool_end",
            "name": "navigate_to_section",
            "data": {"output": _FakeToolOutput(json.dumps({"target": "hero"}))},
        },
        {
            "event": "on_tool_end",
            "name": "search_resume",
            "data": {"output": _FakeToolOutput(json.dumps({"result": "irrelevant"}))},
        },
    ]
    for event in events:
        yield event

async def _collect(input_state, config):
    return [line async for line in stream_chat_response(input_state, config)]

def test_stream_chat_response_filters_classifier_and_maps_tool_actions():

    with patch("streaming.ndjson.graph") as fake_graph:
        fake_graph.astream_events = _fake_astream_events
        fake_graph.aget_state = AsyncMock(return_value=_FakeStateSnapshot())
 
        lines = asyncio.run(_collect({"messages": []}, {"configurable": {"thread_id": "t"}}))
 
    parsed = [json.loads(line) for line in lines]
 
    # classify_intent's raw structured-output token never reaches the client
    text_events = [e for e in parsed if e["type"] == "text"]
    assert all(e["content"] != '{"route":"qa"}' for e in text_events)
    assert any(e["content"] == "Hello!" for e in text_events)
 
    # navigate_to_section becomes an action; the unmapped tool doesn't
    action_events = [e for e in parsed if e["type"] == "action"]
    assert len(action_events) == 1
    assert action_events[0]["action"] == "navigate"
    assert action_events[0]["target"] == "hero"
 
    # always ends with done
    assert parsed[-1] == {"type": "done"}


# Endpoint API test
client = TestClient(app)

def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_password_endpoint_wrong_password():
    response = client.post(
        "/api/auth/password",
        json={"thread_id": "http-thread-1", "password": "wrong"},
    )
    assert response.status_code == 401

def test_password_endpoint_correct_password_returns_thread_id():
    response = client.post(
        "/api/auth/password",
        json={"thread_id": "http-thread-2", "password": os.environ["CHAT_PASSWORD"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["authorized"] is True
    assert body["thread_id"] == "http-thread-2"

def test_chat_endpoint_rejects_unauthorized_thread_without_byok():
    response = client.post("/api/chat", json={"thread_id": "http-thread-3", "message": "hi"})
    assert response.status_code == 401

def test_chat_endpoint_rejects_malformed_byok_key():
    response = client.post(
        "/api/chat",
        json={
            "thread_id": "http-thread-4",
            "message": "hi",
            "provider": "openai",
            "api_key": "not-a-real-key",
        },
    )
    assert response.status_code == 400



#------------------------------------

