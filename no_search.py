"""LiteLLM pre-call hook: no server-side web search or fetch through the proxy.

The run sandbox blocks an agent's own network access, but some agents search
the web *through the model API*: Claude Code's WebSearch sends Anthropic's
`web_search_*` server tool, Gemini CLI's google_web_search sends Gemini's
`googleSearch` tool, and OpenAI-style clients can send `web_search_options`.
The request reaches the proxy on localhost, which the sandbox allows, and the
upstream runs the search outside it. In October 2026 runs that returned
published SWE-bench patches for the very task being solved.

So the proxy takes those tools out of every request. A request that asked for
nothing but a search is refused outright, so the agent sees its tool fail
instead of the model answering as if it had searched. proxy.sh puts this file
next to the generated config, where litellm.yaml's `callbacks` finds it.
"""

import sys

# Server-side tool types (Anthropic, OpenAI Responses) that fetch from the web.
SEARCH_TYPES = ("web_search", "web_fetch", "google_search", "url_context")
# Gemini declares built-in tools as keys of a tool object.
SEARCH_KEYS = ("googleSearch", "google_search", "googleSearchRetrieval", "google_search_retrieval",
               "urlContext", "url_context")


def is_search_tool(tool):
    """A server-side search or fetch tool. Client-side tools (OpenAI
    `function`, Anthropic tools with an `input_schema`) run inside the agent,
    where the sandbox already blocks the network, so they stay."""
    if not isinstance(tool, dict):
        return False
    if any(k in tool for k in SEARCH_KEYS):
        return True
    kind = str(tool.get("type") or "")
    if kind in ("function", "custom") or "input_schema" in tool:
        return False
    return kind.startswith(SEARCH_TYPES)


def strip_search(data):
    """Remove server-side search from a request body in place. Returns what was
    removed and whether the request asked for nothing else."""
    removed = []
    if data.pop("web_search_options", None) is not None:
        removed.append("web_search_options")
    tools = data.get("tools")
    only_search = False
    if isinstance(tools, list) and tools:
        kept = [t for t in tools if not is_search_tool(t)]
        if len(kept) < len(tools):
            removed += [str(t.get("type") or t.get("name") or next(iter(t), "?")) for t in tools if is_search_tool(t)]
            only_search = not kept
            if kept:
                data["tools"] = kept
            else:
                data.pop("tools", None)
                data.pop("tool_choice", None)
    choice = data.get("tool_choice")
    if isinstance(choice, dict) and str(choice.get("name") or choice.get("type") or "").startswith(SEARCH_TYPES):
        data.pop("tool_choice", None)
    return removed, only_search


try:
    from litellm.integrations.custom_logger import CustomLogger
except ImportError:  # imported by the tests without LiteLLM
    CustomLogger = object


class NoSearch(CustomLogger):
    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        removed, only_search = strip_search(data)
        if removed:
            print(f"no_search: removed {', '.join(removed)} from a {call_type} request", file=sys.stderr, flush=True)
        if only_search:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="web search is disabled in this benchmark: "
                                "solve the task from the repository")
        return data


proxy_handler_instance = NoSearch()
