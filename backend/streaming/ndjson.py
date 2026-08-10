import json
from agents.graph import graph
from typing import Any, AsyncGenerator
from langgraph.types import Command

TOOL_ACTION_MAP = {
    "navigate_to_section": "navigate",
    "send_cv_email": "email",
}

STREAMING_NODES = {"qa_agent", "deep_dive_agent"}


def _serialize_tool_output(output : Any) -> dict:

    if isinstance(output, Command):
        messages = (output.update or {}).get("messages", [])
    if messages:
        content = getattr(messages[-1], "content", None)
        if isinstance(content, str):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"raw": content}

    content = getattr(output,"content",output)
    if isinstance(content, dict):
        return content
    try :
        return json.loads(content)
    except (TypeError, json.JSONDecodeError):
        return {"raw": content}
    

async def stream_chat_response(input_state, config):
    try :
        async for event in graph.astream_events(input_state, config, version="v2"):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                node = event.get("metadata", {}).get("langgraph_node")
                if node not in STREAMING_NODES:
                    continue
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield json.dumps({"type": "text", "content": chunk.content}) + "\n"

            elif kind == "on_tool_end" and event["name"]:
                action = TOOL_ACTION_MAP.get(event["name"])
                if action is None :
                    continue

                fields = _serialize_tool_output(event["data"]["output"])
                yield json.dumps({"type": "action", "action": action, **fields}) + "\n"
    except Exception as exc :
        yield json.dumps({"type": "error", "message": str(exc)}) + "\n"

    state = await graph.aget_state(config)
    if state.next:
        for task in state.tasks:
            for intr in getattr(task, "interrupts", None) or []:
                yield json.dumps(
                    {"type": "interrupt", "action": "confirm_email", "data": intr.value}
                ) + "\n"
 
    yield json.dumps({"type": "done"}) + "\n"




