import os
import re
import time
from dataclasses import dataclass


from dotenv import load_dotenv
from fastapi import HTTPException, Request

load_dotenv()


PASSWORD = os.environ.get("CHAT_PASSWORD")

MAX_ATTEMPT = 5
LOCKOUT_TIME_SECONDS = 15*60 

@dataclass
class _AttemptRecord:
    count : int = 0
    locked_until : float = 0.0

_attempts : dict[str, _AttemptRecord] = {}

_authorized_threads: set[str] = set()

def _client_id(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded :
        return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "unknow"

def check_password(request: Request, thread_id: str, password: str) -> None :
    if not PASSWORD :
        raise HTTPException(
            status_code= 500,
            detail = "Server misconfigured: CHAT_PASSWORD is not set"
        )

    client_id = _client_id(request)
    record = _attempts.setdefault(client_id, _AttemptRecord())

    now = time.time()

    retry_after = int(record.locked_until - now)

    if record.locked_until > now :
        retry_after = int(record.locked_until - now)
        raise HTTPException(
            status_code=429,
            detail = f"Too many failed attempt, try again after {retry_after}s",
            headers = {"Retry-After":str(retry_after)},
        )

    if password != PASSWORD :
        record.count += 1
        if record.count >= MAX_ATTEMPT:
            record.locked_until = now + LOCKOUT_TIME_SECONDS
            record.count = 0
            raise HTTPException(
                status_code=429,
                detail = f"Too many failed attempt, Locked for {LOCKOUT_TIME_SECONDS // 60} minutes ",
                headers = {"Retry-After":str(retry_after)},
            )

        remaining = MAX_ATTEMPT - record.count
        
        raise HTTPException(
            status_code=401,
            detail = f"Incorrect password. {remaining} attempt(s) remaining before lockout",
        )

    record.count = 0
    _authorized_threads.add(thread_id)

def is_authorized(thread_id:str) -> bool:
    return thread_id in _authorized_threads


#------ BYOK -----------------

_KEY_PATTERNS = {
    "openai": re.compile(r"^sk-[A-Za-z0-9_-]{20,}$"),
    "anthropic": re.compile(r"^sk-ant-[A-Za-z0-9_-]{20,}$"),
    "gemini": re.compile(r"^AIza[A-Za-z0-9_-]{20,}$"),
}

def validate_byok(provider: str | None, api_key: str | None) -> None:
    if not provider or not api_key:
        raise HTTPException(
            status_code=401,
            detail="Provide either the site password or your own provider + api_key.",
        )
    if provider not in _KEY_PATTERNS:
        supported = ", ".join(_KEY_PATTERNS)
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider '{provider}'. Supported: {supported}.",
        )
    if not _KEY_PATTERNS[provider].match(api_key):
        raise HTTPException(
            status_code=400,
            detail=f"That doesn't look like a valid {provider} API key.",
        )


def require_access(
    request: Request,
    thread_id: str,
    provider: str|None,
    api_key: str|None,
) -> None:
    if is_authorized(thread_id):
        return
    validate_byok(provider, api_key)