
# Portfolio/backend/tests/test_resume_tools.py
import os
from dotenv import load_dotenv
import asyncio
import json
import base64

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

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
#
from agents import search_resume, navigate_to_section, send_cv_email
from agents import (
    _repos_cache,
    _repo_details_cache,
    _log_failed_email,
    EMAIL_DB_PATH,
)
import sqlite3

# ===========================================================================
# search_resume — fix the assertion-less test, add the "not found" branch
# ===========================================================================

def test_search_resume_tool_returns_relevant_chunk():
    """The original version of this test called .invoke() but asserted
    nothing, so it would pass even if search_resume returned garbage or
    raised silently-swallowed errors. This checks real content came back."""
    from agents import search_resume

    query = "What languages does Michael speak besides English?"
    result = search_resume.invoke({"query": query})

    assert isinstance(result, str)
    assert result != ""
    assert "NOT_FOUND" not in result
    # Loose content check — avoids being brittle to embedding-model drift
    assert "Vietnamese" in result or "Chinese" in result or "Finnish" in result


def test_search_resume_tool_not_found_when_no_matches():
    """Exercises the NOT_FOUND fallback branch, which the happy-path test
    never touches. Mocks the vector store directly rather than relying on
    a query that's *hopefully* irrelevant enough to return nothing."""
    from agents import search_resume

    with patch("agents.tools._vector_store") as fake_store:
        fake_store.similarity_search.return_value = []
        result = search_resume.invoke({"query": "anything"})

    assert "NOT_FOUND" in result
    assert "not sure" in result.lower() or "email" in result.lower()


def test_search_resume_tool_includes_header_path_in_output():
    """Confirms the h1/h2/h3 metadata join logic actually runs and prefixes
    the chunk, since a wrong metadata key silently drops the header path."""
    from agents import search_resume

    fake_doc = MagicMock()
    fake_doc.metadata = {"h1": "Core Technical Skills"}
    fake_doc.page_content = "AI & Agentic Workflows: LangGraph, LangChain..."

    with patch("agents.tools._vector_store") as fake_store:
        fake_store.similarity_search.return_value = [fake_doc]
        result = search_resume.invoke({"query": "what AI tools does he use"})

    assert "Core Technical Skills" in result
    assert "LangGraph" in result


# ===========================================================================
# navigate_to_section — completely untested before this
# ===========================================================================

def test_navigate_to_section_tool_returns_ok_status_and_target():
    from agents import navigate_to_section

    result = navigate_to_section.invoke({"target": "experience"})

    assert result["status"] == "ok"
    assert result["target"] == "experience"


def test_navigate_to_section_tool_rejects_unknown_target():
    """target is typed as SessionId (per schemas/tool.py) rather than a
    bare str, so an ID outside Table 1 should fail schema validation
    instead of silently returning a target the frontend has no selector
    for. If SessionId isn't a constrained Literal/enum, this test will
    fail and is a signal to tighten the schema."""
    from agents import navigate_to_section
    from pydantic import ValidationError as PydanticValidationError

    with pytest.raises((PydanticValidationError, Exception)):
        navigate_to_section.invoke({"target": "not-a-real-section"})


# ===========================================================================
# send_cv_email — the biggest gap. Session limit, interrupt confirm/cancel,
# malformed interrupt payload, and exhausted retries all need coverage.
# ===========================================================================

@pytest.fixture
def base_email_config():
    return {"configurable": {"thread_id": "email-test-thread"}}


def _invoke_send_cv_email(recipient_email, emails_sent, config, tool_call_id="call-1", recipient_name=None):
    from agents import send_cv_email
    return send_cv_email.invoke(
        {
            "recipient_email": recipient_email,
            "recipient_name": recipient_name,
            "state": {"messages": [], "emails_sent_this_session": emails_sent},
            "tool_call_id": tool_call_id,
        },
        config=config,
    )


def test_send_cv_email_tool_blocks_when_session_limit_reached(base_email_config):
    """At MAX_EMAILS_PER_SESSION, the tool should short-circuit to
    'cancelled' *before* ever calling interrupt() -- otherwise the user
    gets prompted to confirm an email that will never send."""
    with patch("agents.tools.interrupt") as fake_interrupt:
        command = _invoke_send_cv_email("hr@example.com", emails_sent=5, config=base_email_config)

    fake_interrupt.assert_not_called()
    tool_msg = command.update["messages"][0]
    payload = json.loads(tool_msg.content)
    assert payload["status"] == "cancelled"
    assert "max number" in payload["message"].lower()


def test_send_cv_email_tool_sends_on_confirmation(base_email_config):
    """Happy path: interrupt returns a confirm decision, the send succeeds
    on the first try, and the session counter increments."""
    with patch("agents.tools.interrupt", return_value={"recipient_email": "hr@example.com", "action": "confirm"}), \
         patch("agents.tools._send_email_with_resend") as fake_send:
        command = _invoke_send_cv_email("hr@example.com", emails_sent=0, config=base_email_config)

    fake_send.assert_called_once_with("hr@example.com", None)
    tool_msg = command.update["messages"][0]
    payload = json.loads(tool_msg.content)
    assert payload["status"] == "sent"
    assert command.update["emails_sent_this_session"] == 1


def test_send_cv_email_tool_cancelled_on_user_decline(base_email_config):
    with patch("agents.tools.interrupt", return_value={"recipient_email": "hr@example.com", "action": "cancel"}), \
         patch("agents.tools._send_email_with_resend") as fake_send:
        command = _invoke_send_cv_email("hr@example.com", emails_sent=0, config=base_email_config)

    fake_send.assert_not_called()
    tool_msg = command.update["messages"][0]
    payload = json.loads(tool_msg.content)
    assert payload["status"] == "cancelled"
    # cancelling shouldn't consume a session slot
    assert "emails_sent_this_session" not in command.update


def test_send_cv_email_tool_handles_malformed_interrupt_payload(base_email_config):
    """If whatever resumes the interrupt() doesn't match
    SendCvEmailConfirmation's schema (e.g. a plain string, or a dict
    missing `action`), the tool should degrade to 'cancelled' rather than
    raising an unhandled ValidationError up through the graph."""
    with patch("agents.tools.interrupt", return_value="yes please"), \
         patch("agents.tools._send_email_with_resend") as fake_send:
        command = _invoke_send_cv_email("hr@example.com", emails_sent=0, config=base_email_config)

    fake_send.assert_not_called()
    tool_msg = command.update["messages"][0]
    payload = json.loads(tool_msg.content)
    assert payload["status"] == "cancelled"
    assert "confirmation" in payload["message"].lower()


def test_send_cv_email_tool_logs_to_sqlite_after_exhausting_retries(base_email_config, tmp_path):
    """Forces every send attempt to fail and checks the SQLite fallback
    actually gets a row -- this is the one branch that silently fails in
    production if _log_failed_email's SQL or path is wrong, since the
    tool still returns a friendly message either way."""
    import time as time_module

    test_db = tmp_path / "failed_emails_test.db"

    with patch("agents.tools.interrupt", return_value={"recipient_email": "hr@example.com", "action": "confirm"}), \
         patch("agents.tools._send_email_with_resend", side_effect=RuntimeError("resend down")), \
         patch("agents.tools.EMAIL_DB_PATH", str(test_db)), \
         patch("agents.tools.time.sleep"):  # skip real exponential backoff delays
        command = _invoke_send_cv_email("hr@example.com", emails_sent=0, config=base_email_config)

    tool_msg = command.update["messages"][0]
    payload = json.loads(tool_msg.content)
    assert payload["status"] == "failed_will_retry_log"

    conn = sqlite3.connect(str(test_db))
    try:
        rows = conn.execute(
            "SELECT recipient_email, status, retry_count FROM failed_email_log WHERE recipient_email = ?",
            ("hr@example.com",),
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 1
    assert rows[0][1] == "pending"
    assert rows[0][2] == 5  # MAX_SEND_RETRIES


# ===========================================================================
# get_github_repos — cache hit/miss behavior was never verified
# ===========================================================================

@pytest.fixture(autouse=True)
def reset_github_caches():
    """Module-level caches persist across tests and will make a 'cache
    miss' test pass for the wrong reason if a prior test already warmed
    it. Same idea as your auth reset_auth_state fixture."""
    from agents.tools import _repos_cache, _repo_details_cache
    _repos_cache["data"] = None
    _repos_cache["timestamp"] = 0
    _repo_details_cache.clear()
    yield
    _repos_cache["data"] = None
    _repos_cache["timestamp"] = 0
    _repo_details_cache.clear()


_FAKE_REPOS_JSON = [
    {
        "name": "portfolio", "description": "desc", "language": "Python",
        "stargazers_count": 3, "html_url": "https://github.com/x/portfolio",
        "topics": ["ai"], "updated_at": "2026-01-01T00:00:00Z", "fork": False,
    }
]


def test_get_github_repos_tool_uses_cache_on_second_call():
    from agents import get_github_repos

    fake_response = MagicMock()
    fake_response.json.return_value = _FAKE_REPOS_JSON
    fake_response.raise_for_status.return_value = None

    with patch("agents.tools.httpx.get", return_value=fake_response) as fake_get:
        first = get_github_repos.invoke({})
        second = get_github_repos.invoke({})

    fake_get.assert_called_once()  # second call should hit the cache, not the network
    assert first == second


def test_get_github_repos_tool_refetches_after_cache_expiry():
    from agents import get_github_repos
    import agents.tools as tools_module

    fake_response = MagicMock()
    fake_response.json.return_value = _FAKE_REPOS_JSON
    fake_response.raise_for_status.return_value = None

    with patch("agents.tools.httpx.get", return_value=fake_response) as fake_get:
        get_github_repos.invoke({})
        # simulate the TTL having elapsed
        tools_module._repos_cache["timestamp"] -= (tools_module.CACHE_TTL_SECONDS + 1)
        get_github_repos.invoke({})

    assert fake_get.call_count == 2


def test_get_github_repos_tool_skips_forks():
    from agents import get_github_repos

    forked = dict(_FAKE_REPOS_JSON[0])
    forked["name"] = "some-fork"
    forked["fork"] = True

    fake_response = MagicMock()
    fake_response.json.return_value = _FAKE_REPOS_JSON + [forked]
    fake_response.raise_for_status.return_value = None

    with patch("agents.tools.httpx.get", return_value=fake_response):
        repos = get_github_repos.invoke({})

    assert all(r.name != "some-fork" for r in repos)


# ===========================================================================
# get_repo_details — 404 handling and caching were never verified
# ===========================================================================

def test_get_repo_details_tool_404_returns_available_repos():
    """This is the exact 'catch the 404, suggest what does exist' behavior
    called out in Portfolio_Website.md, and it was never actually tested."""
    from agents import get_repo_details

    not_found_response = MagicMock(status_code=404)

    fake_repos_response = MagicMock()
    fake_repos_response.json.return_value = _FAKE_REPOS_JSON
    fake_repos_response.raise_for_status.return_value = None

    with patch("agents.tools.httpx.get", side_effect=[not_found_response, fake_repos_response]):
        result = get_repo_details.invoke({"repo_name": "does-not-exist"})

    assert result["error"] == "not_found"
    assert "does-not-exist" in result["message"]
    assert "portfolio" in result["available_repos"]


def test_get_repo_details_tool_uses_cache_on_second_call():
    from agents import get_repo_details

    repo_response = MagicMock(status_code=200)
    repo_response.json.return_value = {
        "name": "portfolio", "description": "d", "language": "Python",
        "stargazers_count": 1, "html_url": "https://github.com/x/portfolio",
        "topics": [], "updated_at": "2026-01-01T00:00:00Z",
    }
    repo_response.raise_for_status.return_value = None

    langs_response = MagicMock(status_code=200)
    langs_response.json.return_value = {"Python": 1000}

    readme_response = MagicMock(status_code=200)
    readme_response.json.return_value = {"content": base64.b64encode(b"# Portfolio\nHello").decode()}

    with patch(
        "agents.tools.httpx.get",
        side_effect=[repo_response, langs_response, readme_response],
    ) as fake_get:
        first = get_repo_details.invoke({"repo_name": "portfolio"})
        second = get_repo_details.invoke({"repo_name": "portfolio"})

    assert fake_get.call_count == 3  # repo + languages + readme, once total
    assert first is second


def test_get_repo_details_tool_readme_excerpt_is_decoded_and_truncated():
    from agents import get_repo_details

    repo_response = MagicMock(status_code=200)
    repo_response.json.return_value = {
        "name": "portfolio", "description": None, "language": "Python",
        "stargazers_count": 0, "html_url": "https://github.com/x/portfolio",
        "topics": [], "updated_at": "2026-01-01T00:00:00Z",
    }
    repo_response.raise_for_status.return_value = None

    langs_response = MagicMock(status_code=200)
    langs_response.json.return_value = {}

    long_readme = "A" * 2000
    readme_response = MagicMock(status_code=200)
    readme_response.json.return_value = {"content": base64.b64encode(long_readme.encode()).decode()}

    with patch("agents.tools.httpx.get", side_effect=[repo_response, langs_response, readme_response]):
        details = get_repo_details.invoke({"repo_name": "portfolio"})

    assert len(details.readme_excerpt) == 1500
    assert details.readme_excerpt == long_readme[:1500]