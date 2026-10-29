"""Tests for no_search.py, the proxy hook that refuses server-side web search."""
import unittest

from no_search import is_search_tool, strip_search


class NoSearchTest(unittest.TestCase):
    def test_claude_code_websearch_request_is_only_search(self):
        # What Claude Code's WebSearch sends: Anthropic's server tool and nothing else.
        body = {"messages": [{"role": "user", "content": "Perform a web search for the query: x"}],
                "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}]}
        removed, only = strip_search(body)
        self.assertEqual(removed, ["web_search_20250305"])
        self.assertTrue(only)
        self.assertNotIn("tools", body)

    def test_client_tools_stay(self):
        bash = {"name": "Bash", "description": "run", "input_schema": {"type": "object"}}
        fn = {"type": "function", "function": {"name": "web_search", "parameters": {}}}
        fetch = {"type": "web_fetch_20250910", "name": "web_fetch"}
        body = {"tools": [bash, fn, fetch], "tool_choice": {"type": "auto"}}
        removed, only = strip_search(body)
        self.assertEqual(removed, ["web_fetch_20250910"])
        self.assertFalse(only)
        # The agent's own tools run inside the sandbox, where the network is blocked.
        self.assertEqual(body["tools"], [bash, fn])
        self.assertEqual(body["tool_choice"], {"type": "auto"})

    def test_gemini_google_search_and_openai_options(self):
        body = {"tools": [{"googleSearch": {}}], "web_search_options": {"search_context_size": "low"}}
        removed, only = strip_search(body)
        self.assertEqual(removed, ["web_search_options", "googleSearch"])
        self.assertTrue(only)
        self.assertEqual(body, {})
        # OpenAI Responses' built-in search.
        self.assertTrue(is_search_tool({"type": "web_search_preview"}))
        self.assertFalse(is_search_tool({"type": "function", "name": "google_search"}))

    def test_requests_without_search_are_untouched(self):
        body = {"messages": [], "tools": [{"type": "function", "function": {"name": "Read"}}]}
        before = dict(body)
        self.assertEqual(strip_search(body), ([], False))
        self.assertEqual(body, before)


if __name__ == "__main__":
    unittest.main()
