from pathlib import Path
from typing import Literal, Annotated
import os
import sqlite3
from datetime import datetime, timezone
import logging
import time
import httpx
import base64



from pydantic import BaseModel, Field,EmailStr,ValidationError
import resend
from langchain.tools import tool, InjectedToolCallId
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langgraph.prebuilt import InjectedState
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt, Command
from langchain_core.messages import ToolMessage

from schemas.tool import NavigateToSectionInput,SessionId
from schemas.tool import SendCvEmailInput,SendCvEmailResult,SendCvEmailConfirmation
from schemas.tool import RepoSummary,RepoDetails

# RAG on resume Start --------------------------------------------------------

HEADER_TO_SPLIT = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3")
]
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_PERSIST_DIRECTORY = Path(__file__).parent.parent/'db'/'chroma_store'
TOP_K = 3
RESUME_PATH = Path(__file__).resolve().parent.parent.parent / \
    "local_info" / "resume-no-password.md"

_embedding: HuggingFaceEmbeddings | None = None


def get_embedding_model() -> HuggingFaceEmbeddings:
    global _embedding
    if _embedding is None:
        _embedding = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embedding


def read_and_format_resume(resume_path):
    docs = ''
    with open(resume_path, "r") as f:
        resume_text = f.read()

        text_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=HEADER_TO_SPLIT,
            strip_headers=False
        )
        docs = text_splitter.split_text(resume_text)
    return docs


def vector_store_embedding(force_rebuilt: bool = False) -> Chroma:
    embedding = get_embedding_model()

    # Store the embeddings in the vector store
    vector_store = Chroma(
        collection_name="resume",
        embedding_function=embedding,
        persist_directory=str(CHROMA_PERSIST_DIRECTORY)
    )

    existing_count = 0

    if existing_count == 0 and force_rebuilt:
        vector_store.delete_collection()
        vector_store = Chroma(
            collection_name="resume",
            embedding_function=embedding,
            persist_directory=str(CHROMA_PERSIST_DIRECTORY)
        )

    if existing_count == 0:
        docs = read_and_format_resume(RESUME_PATH)
        vector_store.add_documents(docs)

    return vector_store


_vector_store = vector_store_embedding(force_rebuilt=False)


@tool
def search_resume(query: str) -> str:
    """
    Search resume knowledge base for information,elevant to the user's question
    - experience, skills, education, certifications, projects, or contact info.

    Use this any time the user asks about Michael's background, work history, technical skills, 
    or qualifications that isn't already established in the conversation.

    Args:
        query: The user's question or topic, e.g. "What AI frameworks
               does he use?" or "Tell me about his homelab."

    Returns:
            The most relevant resume section(s) as plain text, or a message
            indicating nothing relevant was found.

    """

    results = _vector_store.similarity_search(query, k=TOP_K)

    if not results:
        return (
            "NOT_FOUND: nothing relevant in the knowledge base. "
            "Tell the user you're not sure and offer to connect them via email."
        )

    chunks = []
    for doc in results:
        header_path = " > ".join(
            v for k, v in doc.metadata.items() if k in ("h1", "h2", "h3")
        )
        text = doc.page_content.strip()
        chunks.append(f"{header_path}\n{text}" if header_path else text)

    return "\n\n---\n\n".join(chunks)

# RAG on resume End --------------------------------------------------------

@tool(args_schema=NavigateToSectionInput)
def navigate_to_section(target: SessionId) -> dict:
    """Scroll the user's browser to a specific section of the portfolio page."""
    
    return {"status": "ok", "target": target}


# send_cv_email tool Start --------------------------------------------------------

logger = logging.getLogger(__name__)


resend.api_key = os.environ["RESEND_API_KEY"]

CV_SENDER_EMAIL = os.environ["CV_SENDER_EMAIL"]
PERSONAL_EMAIL = os.environ["PERSONAL_EMAIL"]
CV_PDF_PATH = os.environ["CV_PDF_PATH"]

MAX_EMAILS_PER_SESSION = 5
MAX_SEND_RETRIES = 5
RETRY_BACKOFF_BASE_SECONDS = 2

EMAIL_DB_PATH = os.environ["EMAIL_DB_PATH"]

def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(EMAIL_DB_PATH)
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS failed_email_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_email TEXT NOT NULL,
            user_prompt TEXT,              -- the message that triggered the send request, for context
            thread_id TEXT,                -- session that generated this, useful for debugging
            retry_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'sent' | 'abandoned'
            created_at TEXT NOT NULL,      -- ISO timestamp, first failure
            last_attempted_at TEXT NOT NULL,
            resolved_at TEXT               -- NULL until sent or abandoned
        );
        '''
    )

    return conn

def _log_failed_email(recipient_email: str, user_prompt: str | None, thread_id: str,retry_count: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_db()
    try:
        conn.execute(
            """
            INSERT INTO failed_email_log
            (recipient_email, user_prompt, thread_id, retry_count, status, created_at, last_attempted_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?)""",
            (recipient_email, user_prompt, thread_id, retry_count, now, now)
        )
        conn.commit()
    finally:
        conn.close()

def _last_user_text(state: dict) -> str | None:
    """
    Extract the last user message from the conversation state.
    """
    for msg in reversed(state.get("messages", [])):
        role = getattr(msg, "type", None) or (msg.get("role") if isinstance(msg, dict) else None)
        if role in ("human", "user"):
            return getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None)
    return None

def _send_email_with_resend(recipient_email: str, recipient_name: str | None) -> None:
    # Implementation for sending email with Resend
    with open(CV_PDF_PATH, "rb") as cv_file:
        cv_content = cv_file.read()
    
    greeting = f"Dear {recipient_name}," if recipient_name else "Hello,"

    resend.Emails.send({
        "from": f"Ân (Michael) Nguyen <{CV_SENDER_EMAIL}>",
        "to": [recipient_email],
        "subject": "Ân (Michael) Nguyen — Resume / CV",
        "html": (
            f"<p>{greeting}</p>"
            "<p>Thanks for chatting with my portfolio assistant — my resume is attached.</p>"
            "<p>Happy to answer any follow-up questions by email.</p>"
            "<p>Best,<br/>Ân (Michael) Nguyen</p>"
        ),
        "attachments": [{
            "filename": "Michael_Nguyen_Resume.pdf",
            "content": list(cv_content),
        }],
    })


@tool(args_schema = SendCvEmailInput)
def send_cv_email(
    recipient_email : str ,
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    recipient_name : str | None = None,


    ) -> dict:
    """
    Email Michael's CV/resume as a PDF to the given address.

    This tool pauses execution for an explicit human confirmation before
    anything is actually sent — call it as soon as you have a valid email
    address, and let the interrupt handle the "are you sure" step rather
    than trying to confirm in conversation first.
    """
    thread_id = config["configurable"].get("thread_id", "unknown")
    emails_sent = state.get("emails_sent_this_session", 0)

    # Check if user session has exceeded the maximum number of email attempts
    if emails_sent >= MAX_EMAILS_PER_SESSION:
            result = SendCvEmailResult(
                status="cancelled",
                recipient_email=recipient_email,
                message=(
                    "I've already sent the max number of CVs for this session. "
                    f"Feel free to email me directly at {PERSONAL_EMAIL} and I'll follow up."
                ),
            )
            return Command(update={
                "messages": [ToolMessage(content=result.model_dump_json(), tool_call_id=tool_call_id)],
            })
    # Human in the loop
    raw_decision = interrupt({
        "type": "action",
        "action": "confirm_send_cv_email",
        "recipient_email": recipient_email,
        "recipient_name": recipient_name,
        "message": f"Send the CV to {recipient_email}?",
    })
    try:
        confirmation = SendCvEmailConfirmation.model_validate(raw_decision)
    except ValidationError:
        result = SendCvEmailResult(
            status="cancelled",
            recipient_email=recipient_email,
            message="I didn't get a clear confirmation, so I held off on sending anything.",
        )
        return Command(update={
            "messages": [ToolMessage(content=result.model_dump_json(), tool_call_id=tool_call_id)],
        })
    if confirmation.action == "cancel":
        result = SendCvEmailResult(
            status="cancelled",
            recipient_email=recipient_email,
            message="No problem — let me know if you'd like me to send it later.",
        )
        return Command(update={
            "messages": [ToolMessage(content=result.model_dump_json(), tool_call_id=tool_call_id)],
        })


        last_error: Exception | None = None
    for attempt in range(1, MAX_SEND_RETRIES + 1):
        try:
            _send_email_with_resend(recipient_email, recipient_name)
            result = SendCvEmailResult(
                status="sent",
                recipient_email=recipient_email,
                message="Sent! Check your inbox (and spam folder, just in case).",
            )
            return Command(update={
                "emails_sent_this_session": emails_sent + 1,
                "messages": [ToolMessage(content=result.model_dump_json(), tool_call_id=tool_call_id)],
            })
        except Exception as e:
            last_error = e
            logger.warning(
                "send_cv_email attempt %d/%d failed for %s: %s",
                attempt, MAX_SEND_RETRIES, recipient_email, e,
            )
            if attempt < MAX_SEND_RETRIES:
                time.sleep(RETRY_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)))
    
    _log_failed_email(
        recipient_email=recipient_email,
        user_prompt=_last_user_text(state),
        thread_id=thread_id,
        retry_count=MAX_SEND_RETRIES,
    )
    logger.error("send_cv_email exhausted retries for %s: %s", recipient_email, last_error)
    result = SendCvEmailResult(
        status="failed_will_retry_log",
        recipient_email=recipient_email,
        message=(
            "I couldn't get the email out just now, but I've logged it and it'll go out "
            f"soon as long as that address is valid. You can also reach me directly at {PERSONAL_EMAIL}."
        ),
    )

    return Command(update={
        "emails_sent_this_session": emails_sent + 1,
        "messages": [ToolMessage(content=result.model_dump_json(), tool_call_id=tool_call_id)],
    })
# send_cv_email tool End --------------------------------------------------------

# get_github_repos / get_repo_details Start --------------------------------
GITHUB_USERNAME = "NMichaelg"
GITHUB_TOKEN = os.environ["GITHUB_PAT"]
CACHE_TTL_SECONDS = 60 * 60  # 1 hour

_repos_cache: dict = {"data" : None, "timestamp": 0}
_repo_details_cache: dict[str,dict] = {}

GITHUB_HEADER = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}

@tool
def get_github_repos() -> list[RepoSummary]:
    """
    Get the list of Michael's public GitHub repositories, including
    name, description, language, star count, and topics. Use this when
    the user asks what projects Michael has worked on.
    """
    current_time = time.time()

    # If the cache is still valid, return the cached data
    if _repos_cache["data"] is not None \
        and (current_time - _repos_cache["timestamp"]) < CACHE_TTL_SECONDS:

        return _repos_cache["data"]
    
    # If the cache is expired or empty, fetch fresh data from GitHub

    url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
    response = httpx.get(
        url, 
        headers=GITHUB_HEADER,
        params={"sort": "updated","per_page": 100},
        timeout=10
    )
    response.raise_for_status()
    repos_data = response.json()

    summaries = [
        RepoSummary(
            name=r["name"],
            description=r.get("description"),
            language=r.get("language"),
            stars=r["stargazers_count"],
            url=r["html_url"],
            topics=r.get("topics", []),
            updated_at=r["updated_at"],
        )
        for r in repos_data
        if not r.get("fork")  # optional: skip forks, keep it curated
    ]

    _repos_cache["data"] = summaries
    _repos_cache["timestamp"] = current_time

    return summaries

@tool
def get_repo_details(repo_name: str) -> RepoDetails | dict:
    """
    Get detailed info about one of Michael's GitHub repos, including
    language breakdown and a README excerpt. Pass just the repo name
    (e.g. 'portfolio-website'), not the full owner/repo path.
    """
    current_time = time.time()
    cached = _repo_details_cache.get(repo_name)

    # If the cache is still valid and contains the requested repo, return the cached data
    if cached and (current_time - cached["timestamp"]) < CACHE_TTL_SECONDS:
        return cached["data"]

    # If the cache is expired or empty, fetch fresh data from GitHub
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}"
    response = httpx.get(url, headers=GITHUB_HEADER, timeout=10)

    if response.status_code == 404:
        existing = get_github_repos.invoke({})
        return {
            "error": "not_found",
            "message": f"No repo named '{repo_name}' found.",
            "available_repos": [r.name for r in existing],
        }
    response.raise_for_status()
    repo_data = response.json()

    langs_resp = httpx.get(f"{url}/languages", headers=GITHUB_HEADER, timeout=10.0)
    languages_breakdown = langs_resp.json() if langs_resp.status_code == 200 else {}

    readme_excerpt = ""
    readme_resp = httpx.get(f"{url}/readme", headers=GITHUB_HEADER, timeout=10.0)

    if readme_resp.status_code == 200:
        decoded = base64.b64decode(readme_resp.json()["content"]).decode("utf-8", errors="ignore")
        readme_excerpt = decoded[:1500]

    details = RepoDetails(
        name=repo_data["name"],
        description=repo_data.get("description"),
        language=repo_data.get("language"),
        languages_breakdown=languages_breakdown,
        stars=repo_data["stargazers_count"],
        url=repo_data["html_url"],
        topics=repo_data.get("topics", []),
        readme_excerpt=readme_excerpt,
        updated_at=repo_data["updated_at"],
    )
    _repo_details_cache[repo_name] = {"data": details, "timestamp": current_time}
    return details

# get_github_repos / get_repo_details END --------------------------------
