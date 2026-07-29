
# Portfolio/backend/tests/test_resume_tools.py
import os
from dotenv import load_dotenv

load_dotenv()

from pathlib import Path
from pprint import pprint
from langchain.messages import HumanMessage

from agents import read_and_format_resume
from agents import get_github_repos, get_repo_details
from agents import graph

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


