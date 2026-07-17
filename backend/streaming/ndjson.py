import json
from agents.graph import graph


TOOL_ACTION_MAP = {
    "navigate_to_section": "navigate",
    "send_cv_email": "email",
}

async def stream_chat_response(input_state, config):
    async for event in graph.astream_events(input_state, config, version="v2"):
        kind = event["event"]

        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if chunk.content:
                yield json.dumps({"type": "text", "content": chunk.content}) + "\n"

        elif kind == "on_tool_end" and event["name"] == "navigate_to_section":
            output = event["data"]["output"]
            content = output.content if isinstance(output.content, dict) else json.loads(output.content)
            yield json.dumps({"type": "action", "action": "navigate", "target": content["target"]}) + "\n"