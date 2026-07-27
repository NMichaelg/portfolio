from langgraph.graph import StateGraph,START,END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from nodes import classify_intent, qa_agent, deep_dive_agent, QA_TOOLS, DEEP_DIVE_TOOLS
from schemas.graph import ChatState, RouteOutput


def route_after_classify(state: ChatState) -> str :
    return "qa_agent" if state["route"] == 'qa' else "deep_dive_agent"


graph_builder = StateGraph(ChatState)

# --- nodes

graph_builder.add_node("classify_intent", classify_intent)
graph_builder.add_node("qa_agent", qa_agent)
graph_builder.add_node("deep_dive_agent", deep_dive_agent)
graph_builder.add_node("qa_tools", ToolNode(QA_TOOLS))
graph_builder.add_node("deep_dive_tools", ToolNode(DEEP_DIVE_TOOLS))

#--- edges

graph_builder.add_edge(START,"classify_intent")

graph_builder.add_conditional_edge(
    "classify_intent",
    route_after_classify,
    {"qa_agent":"qa_agent","deep_dive_agent":"deep_dive_agent"}
)

graph_builder.add_conditional_edge(
    "qa_agent",
    tools_condition,
    {"tools":"qa_tools",END:END}
)

graph_builder.add_edge("qa_tools","qa_agent")

graph_builder.add_conditional_edge(
    "deep_dive_agent",
    tools_condition,
    {"tools":"deep_dive_tools",END:END}
)

graph_builder.add_edge("deep_dive_tools","deep_dive_agent")

#--- Checkpoint

checkpointer = MemorySaver()
graph = graph_builder.compile(checkpointer=checkpointer)

