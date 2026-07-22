from langgraph.graph import StateGraph,START,END
from langchain_core.messages import AIMessage, ToolMessage
from functools import lru_cache
from pathlib import Path


from schemas.graph import ChatState, RouteOutput
from model import llm 
from tools import search_resume, navigate_to_section, send_cv_email
from tools import get_github_repos, get_repo_details


QA_SYSTEM_PROMPT_PATH = Path(__file__).parent / "qa_system_prompt.md"
DEEP_DIVE_SYSTEM_PROMPT_PATH = Path(__file__).parent / "deep_dive_system_prompt.md"

@lru_cache(maxsize=1)
def load_qa_system_prompt() -> str:
    return QA_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
def load_deep_dive_system_prompt() -> str :
    return DEEP_DIVE_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def _filter_foreign_tool_messages(messages: list, allowed_tools: list) -> list:
    """
    Each AIMessage's tool_calls are always homogeneous -- either all from this
    agent's own bound tools, or all foreign (produced by the other agent in an
    earlier turn), since only one tool set is ever bound per node invocation.
    So an all-or-nothing check per AIMessage is sufficient; no partial-trim case exists.
    """
    allowed_names = {t.name for t in allowed_tools}
    filtered = []
    skip_ids = set()

    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            foreign_calls = [tc for tc in msg.tool_calls if tc["name"] not in allowed_names]
            if foreign_calls:
                skip_ids.update(tc["id"] for tc in foreign_calls)
                if len(foreign_calls) == len(msg.tool_calls):
                    continue
        if isinstance(msg, ToolMessage) and msg.tool_call_id in skip_ids:
            continue
        filtered.append(msg)

    return filtered
def classify_intent(state: ChatState) -> dict:
    classifier = llm.with_structured_output(RouteOutput)
    task = """
    Classify which agent should handle this user message:
    - "qa": general questions about background, skills, experience, navigating the site, or requesting the CV/resume
    - "deep_dive": questions about specific GitHub projects/repos, code, or implementation details
    """
    result = classifier.invoke([
        {"role": "system", "content": task},
        {"role": "user", "content": state["messages"][-1].content},
    ])
    state['route'] = result.route
    return {"route": result.route}


QA_TOOLS = [search_resume, navigate_to_section, send_cv_email]

def qa_agent(state: ChatState)-> str :
    qa_agent_llm = llm.bind_tools(QA_TOOLS)
    role_prompt = load_qa_system_prompt()

    messages = _filter_foreign_tool_messages(state["messages"], allowed_tools=QA_TOOLS)

    to_send = [
        {"role":'system','content': role_prompt},
        *messages
    ]

    response = qa_agent_llm.invoke(to_send)

    return {"messages": [response]}

DEEP_DIVE_TOOLS = [get_github_repos, get_repo_details]


def deep_dive_agent(state: ChatState)-> str :
    deep_dive_agent_llm = llm.bind_tools(DEEP_DIVE_TOOLS)
    role_prompt = load_deep_dive_system_prompt()

    messages = _filter_foreign_tool_messages(state["messages"], allowed_tools=DEEP_DIVE_TOOLS)

    to_send = [
        {"role":'system','content': role_prompt},
        *messages
    ]

    response = deep_dive_agent_llm.invoke(to_send)

    return {"messages": [response]}