import os

from langchain.chat_models import ChatOpenAI

LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_BASE_URL = os.envron["LLM_BASE_URL"]

llm = ChatOpenAI(
    model = 'openai/gpt-oss-20b',
    base_url = LLM_BASE_URL,
    api_key = LLM_API_KEY
)

