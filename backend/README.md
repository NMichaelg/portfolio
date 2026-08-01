# Backend — Portfolio Chat Assistant

FastAPI backend powering the AI chat assistant on Michael Nguyen's (Ân Nguyễn's) portfolio site. It runs a LangGraph agent that answers questions about Michael's background (RAG over his resume) and his GitHub projects, streams responses to the frontend as NDJSON, and can email his CV via Resend behind a human-in-the-loop confirmation.

## Tech Stack

- **Python 3.14** (managed with `uv`)
- **FastAPI** + **uvicorn** — HTTP API
- **LangGraph** + **LangChain** — agent orchestration (state graph with checkpoints)
- **ChromaDB** + **sentence-transformers** — vector store for resume RAG
- **Resend** — CV email delivery
- **GitHub REST API** — live repo lookups (via `httpx`)
- **SQLite** — failure log for undelivered CV emails

## Architecture

The chat flow is a single LangGraph state machine (`agents/graph.py`):

![LangGraph agent graph](graph.png)

```
START
  → classify_intent          (routes message to qa or deep_dive)
      ├─ qa_agent            (resume Q&A, page navigation, CV email)
      │     ├─ search_resume            → RAG over Chroma
      │     ├─ navigate_to_section      → scroll portfolio page
      │     └─ send_cv_email            → human-in-the-loop interrupt
      │
      └─ deep_dive_agent     (GitHub project deep-dives)
            ├─ get_github_repos         → list public repos
            └─ get_repo_details         → languages + README excerpt
```

- Each turn starts with `classify_intent`, which picks between the **QA agent** and the **deep-dive agent**.
- Both agents use a shared LLM, bound to their own tool sets. Foreign tool messages are filtered out when context crosses from one agent to the other (`_filter_foreign_tool_messages` in `agents/nodes.py`).
- State is checkpointed per `thread_id` via `MemorySaver`, so multi-turn conversations are preserved (in-memory only; restarting the server clears history).
- `send_cv_email` pauses the graph with an `interrupt` until the frontend resumes it with an explicit confirm/cancel — nothing is sent without user confirmation. Each session is capped at 5 emails.

## Project Structure

```
backend/
├── main.py                    # FastAPI app, CORS, /healthz, /api/chat, /api/auth/password
├── agents/
│   ├── graph.py               # LangGraph state machine (nodes, edges, checkpointer)
│   ├── nodes.py               # classify_intent, qa_agent, deep_dive_agent
│   ├── tools.py               # RAG, navigation, CV email, GitHub tools
│   ├── model.py               # LLM factory (default + BYOK providers)
│   └── *_system_prompt.md     # Agent system prompts
├── schemas/                   # Pydantic models for API, graph state, and tools
├── streaming/ndjson.py        # NDJSON event streaming from graph.astream_events
├── auth/                      # Password auth + BYOK key validation
├── db/chroma_store/           # ChromaDB persistence (gitignored)
├── env_example                # Template for .env
├── test.py / run_test.py      # Pytest suite
└── pyproject.toml             # Project metadata + dependencies (uv)
```

## Prerequisites

- Python 3.14
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`
- An LLM API key (and `LLM_BASE_URL`) — any OpenAI-compatible endpoint, e.g. OpenAI, or a gateway
- A GitHub PAT (for repo lookups)
- A [Resend](https://resend.com) API key (for sending the CV)
- Local files (gitignored):
  - `local_info/resume-no-password.md` — source markdown ingested into Chroma
  - `local_info/Profile.pdf` (or your path from `CV_PDF_PATH`) — the CV attached to emails

## Setup

```bash
# 1. Clone / enter the backend directory
cd backend

# 2. Copy the env template and fill in real values
cp env_example .env

# 3. Install dependencies
uv sync          # or: pip install -r requirements.txt

# 4. (Optional) rebuild the Chroma vector store when the resume changes
#    The store is built automatically on first run if db/chroma_store is empty.
```

## Running

```bash
uv run uvicorn main:app --reload --port 8000
```

The API is served at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

## Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `RESEND_API_KEY` | Yes | Resend API key for sending the CV email |
| `CV_SENDER_EMAIL` | Yes | "From" address for CV emails |
| `PERSONAL_EMAIL` | Yes | Michael's direct email (fallback contact) |
| `CV_PDF_PATH` | Yes | Path to the CV PDF attachment |
| `EMAIL_DB_PATH` | Yes | SQLite path for the failed-email log |
| `GITHUB_PAT` | Yes | GitHub PAT for repo lookups |
| `LLM_API_KEY` | Yes | Default LLM API key |
| `LLM_BASE_URL` | Yes | Base URL of the OpenAI-compatible LLM endpoint |
| `CHAT_PASSWORD` | No | Password to unlock chat (see Access control) |
| `TESTING_ONLY_LLM_API_KEY` | No | Used by the test suite |
| `FRONTEND_ORIGINS` | No | Comma-separated CORS origins (default `http://localhost:3000`) |

## API Endpoints

### `GET /healthz`
Health check. Returns `{"status": "ok"}`.

### `POST /api/auth/password`
Authorize a thread with the site password.

```json
{ "thread_id": "optional", "password": "your_password" }
```

Returns `{"authorized": true, "thread_id": "..."}`. On success the thread is authorized for the rest of the session. Failed attempts are rate-limited (5 attempts, then a 15-minute lockout per client IP).

### `POST /api/chat`
Send a message to the assistant. Returns a streaming **NDJSON** response (`application/x-ndjson`).

```json
{
  "thread_id": "optional (auto-generated if omitted)",
  "message": "What tech stack does Michael use?",
  "provider": "optional (openai | anthropic | google) for BYOK",
  "api_key": "optional, required if provider is set",
  "resume": { "action": "confirm" }   // only when resuming an interrupted action
}
```

**Access control:** a thread must be authorized first — either via `/api/auth/password` (unlocks the default LLM) or by sending `provider` + `api_key` (BYOK). BYOK keys are validated by format (OpenAI `sk-`, Anthropic `sk-ant-`, Google `AIza`) and tested live before use.

**Resuming an interrupted action:** if a previous turn ended on a human-in-the-loop confirmation (e.g. `send_cv_email`), you must send `resume` instead of `message`, matching the confirmation payload:

```json
{
  "thread_id": "...",
  "resume": { "recipient_email": "person@example.com", "action": "confirm" }
}
```

Sending a `message` while a confirmation is pending returns `400`.

### Streaming Events

Each line is a JSON object. Event types:

| Type | Payload | Meaning |
| --- | --- | --- |
| `session` | `{ thread_id }` | First event; thread id for this chat |
| `text` | `{ content }` | Streamed LLM token chunk |
| `action` | `{ action, ... }` | Frontend action: `navigate` (scroll to a section) or `email` (email result) |
| `interrupt` | `{ action: "confirm_email", data }` | CV send awaits confirm/cancel |
| `error` | `{ message }` | An error occurred during streaming |
| `done` | — | Stream finished |

## Running Tests

```bash
uv run pytest test.py -v                # full suite
uv run python run_test.py               # auth/BYOK/chat/streaming smoke tests
```

Tests cover resume splitting/RAG, GitHub tools, auth and BYOK validation, the chat endpoint, and NDJSON streaming. Some tests call live services (GitHub, LLM), so set `TESTING_ONLY_LLM_API_KEY` in `.env` first.

## Notes

- Chat history lives in memory (`MemorySaver`) and resets when the server restarts.
- GitHub repo data and the vector store are cached to avoid hammering APIs.
- `db/chroma_store`, `local_info/`, and `.env` are gitignored — never commit secrets or the vector DB.
