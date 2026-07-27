# Review of `backend/agents/nodes.py`

## Correctness issues


5. **No tool-calling loop** (`nodes.py:74, 92`): `qa_agent_llm.invoke(to_send)` is a single shot — if the model returns `tool_calls`, they're never executed and the agent returns an AIMessage with unfinished tool calls. The graph presumably needs a `tools` node + conditional edge back to the agent (ToolNode / `add_messages` loop). Since `graph.py` is empty, there's currently **no graph at all** — these nodes aren't wired to anything. Confirm this is WIP.

6. **`_filter_foreign_tool_messages` assumption is fragile** (`nodes.py:23-45`): the docstring claims each AIMessage's `tool_calls` are homogeneous, but that's guaranteed only by LangChain's current behavior, not anything in this code. If a future node binds multiple tool sets, the `continue` (skip whole message) plus `skip_ids` approach can still drop ToolMessages from the *kept* tool set. Consider asserting `len(foreign_calls) == len(msg.tool_calls)` and falling back to keeping the message, or rewriting tool_calls to only the allowed ones.

## Style / minor

7. (`nodes.py:19`) Odd spacing: `def load_deep_dive_system_prompt() -> str :` (space before `:`). Inconsistent with the cached version above it.

8. (`nodes.py:63, 81`) Same `-> str :` spacing nit on the agent functions.

9. (`nodes.py:70, 88`) Mixing dict-literal role format (`{"role":'system', ...}`) and passing `BaseMessage` objects in the same list works via LangChain's coercion, but it's inconsistent with the rest of the codebase which uses `AIMessage`/`ToolMessage` objects. Minor readability.

10. (`nodes.py:46`) No blank line between `_filter_foreign_tool_messages` and `classify_intent` — PEP 8 wants 2 between top-level defs.

## The big one

Items 5–6 — confirm `graph.py` being empty is intentional. If the graph wiring is supposed to live there, no tool execution loop exists and `routing` (item 2) and `_filter_foreign_tool_messages` (item 6) won't behave as assumed.
