"""
ChatState — shared graph state for backend/agents/graph.py

This is what flows through every node (router, qa_agent, deep_dive_agent,
tools) and what MemorySaver checkpoints per thread_id.
"""

from typing import Annotated, Literal
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class RouteOutput(TypedDict):
    route: Literal["qa", "deep_dive"]


class ChatState(TypedDict):
    """
    Fields are intentionally minimal — anything that doesn't need to persist
    across turns or influence routing/tools shouldn't live here.
    """
    messages: Annotated[list[BaseMessage], add_messages]

    # Set by the router node every turn. No default/reducer needed since
    # router always overwrites it — there's no "sticky" agent state to merge.
    route: RouteOutput| None

    # Session-scoped counter for send_cv_email's rate limit (max 5/session).
    # Plain int, no custom reducer — nodes that update it (only send_cv_email,
    # via Command(update=...)) always write the full new value, not a delta,
    # so last-write-wins is correct and no merge logic is needed.
    emails_sent_this_session: int