import os

from langchain_openai import ChatOpenAI
from openai import AuthenticationError, APIConnectionError, APIError

LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_BASE_URL = os.environ["LLM_BASE_URL"]

_BYOK_PROVIDER ={
    "openai" : {"base_url" : None, "model":"gpt-4o-mini"},
    "anthropic" : {"base_url" :'https://api.anthropic.com/v1/',"model" : "claude-sonnet-4-6"},
    "google" : {"base_url":'https://generativelanguage.googleapis.com/v1beta/openai',"model":"gemini-3.5-flash"},
}


DEFAULT_LLM = ChatOpenAI(
    model='openai/gpt-oss-20b',
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY
)

def get_llm(config):
    configurable = (config or {}).get("configurable",{})
    provider = configurable.get("provider")
    api_key = configurable.get("api_key")

    if not provider or not api_key:
        return DEFAULT_LLM 

    llm_url = _BYOK_PROVIDER[provider]["base_url"]
    model = _BYOK_PROVIDER[provider]["model"]

    try : 
        llm = ChatOpenAI(
            model = model,
            base_url = llm_url,
            api_key = api_key,
        )
        llm.invoke("Hi")
    except AuthenticationError as e:
        raise ValueError(f"Error 401: Invalid API key{e}") from e
    except APIConnectionError as e:
        raise ConnectionError(f"Could not reach {llm_url}") from e
    except APIError as e:
        raise RuntimeError(f"API error: {e}") from e

    return llm