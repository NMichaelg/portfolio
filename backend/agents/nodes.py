from langgraph.graph import StateGraph,START,END

from schemas.graph import ChatState
from model import llm 



def classify_intent(state : ChatState)-> str :
    classifier = llm