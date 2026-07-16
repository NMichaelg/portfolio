
# Portfolio/backend/tests/test_resume_tools.py

from pathlib import Path
from pprint import pprint

from agents import read_and_format_resume

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

    print(result)
