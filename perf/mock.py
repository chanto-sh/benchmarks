"""Instant OpenAI-compatible mock for timing Chanto itself.

MOCK_REPLY=short   -> one short text reply
MOCK_REPLY=long    -> ~30k tokens of markdown (headings, lists, code) in ~6000 chunks
MOCK_REPLY=tools   -> Read, Grep, Edit tool calls, then a short reply
MOCK_REPLY=bash    -> one Bash call per command in MOCK_COMMANDS (a JSON list), then a short reply
MOCK_REPLY=script  -> one tool call per {"name", "arguments"} in MOCK_SCRIPT (a JSON list), then a short reply
                      (e.g. Read then Edit a file in a real task, to time the verify gate)
"""
import json, os, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODE = os.environ.get("MOCK_REPLY", "short")
STATE = {"n": 0}
LOCK = threading.Lock()

PARA = ("## Section {i}\n\nThe **parser** handles `tokens` and returns a tree. "
        "It walks each node, checks invariants, and *reports* errors with spans.\n\n"
        "- first item with `code`\n- second item\n- third item with a [link](https://example.com)\n\n"
        "```rust\nfn handle_{i}(x: u32) -> u32 {{\n    let y = x * 2;\n    y + {i}\n}}\n```\n\n")


def long_text():
    return "".join(PARA.format(i=i) for i in range(400))


def chunks(text, size=20):
    for i in range(0, len(text), size):
        yield text[i:i + size]


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def do_GET(self):
        body = json.dumps({"data": [{"id": "mock"}], "models": [{"name": "mock"}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        with LOCK:
            STATE["n"] += 1
        n_tool = sum(1 for m in req.get("messages", []) if m.get("role") == "tool")
        events = []
        commands = json.loads(os.environ.get("MOCK_COMMANDS", "[]")) if MODE == "bash" else []
        script = json.loads(os.environ.get("MOCK_SCRIPT", "[]")) if MODE == "script" else []
        if MODE == "bash" and n_tool < len(commands):
            events.append({"choices": [{"delta": {"tool_calls": [{"index": 0, "id": f"c{n_tool}", "type": "function",
                           "function": {"name": "Bash", "arguments": json.dumps({"command": commands[n_tool]})}}]}, "finish_reason": None}]})
            events.append({"choices": [{"delta": {}, "finish_reason": "tool_calls"}]})
        elif MODE == "script" and n_tool < len(script):
            call = script[n_tool]
            events.append({"choices": [{"delta": {"tool_calls": [{"index": 0, "id": f"c{n_tool}", "type": "function",
                           "function": {"name": call["name"], "arguments": json.dumps(call["arguments"])}}]}, "finish_reason": None}]})
            events.append({"choices": [{"delta": {}, "finish_reason": "tool_calls"}]})
        elif MODE == "tools" and n_tool < 3:
            target = os.environ.get("MOCK_FILE", "big.txt")
            calls = [
                {"name": "Read", "arguments": {"file_path": target, "offset": 150000, "limit": 40}},
                {"name": "Grep", "arguments": {"pattern": "line 12345 ", "path": ".", "output_mode": "content"}},
                {"name": "Edit", "arguments": {"file_path": target, "old_string": "line 199999 some text here", "new_string": "line 199999 EDITED"}},
            ][n_tool]
            events.append({"choices": [{"delta": {"tool_calls": [{"index": 0, "id": f"c{n_tool}", "type": "function",
                           "function": {"name": calls["name"], "arguments": json.dumps(calls["arguments"])}}]}, "finish_reason": None}]})
            events.append({"choices": [{"delta": {}, "finish_reason": "tool_calls"}]})
        else:
            text = long_text() if MODE == "long" else "Done."
            for c in chunks(text):
                events.append({"choices": [{"delta": {"content": c}, "finish_reason": None}]})
            events.append({"choices": [{"delta": {}, "finish_reason": "stop"}]})
        events.append({"choices": [], "usage": {"prompt_tokens": 1000, "completion_tokens": 500}})
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        delay = float(os.environ.get("MOCK_DELAY", "0"))
        for e in events:
            data = f"data: {json.dumps(e)}\n\n".encode()
            self.wfile.write(f"{len(data):x}\r\n".encode() + data + b"\r\n")
            if delay:
                self.wfile.flush()
                time.sleep(delay)
        data = b"data: [DONE]\n\n"
        self.wfile.write(f"{len(data):x}\r\n".encode() + data + b"\r\n0\r\n\r\n")
        self.wfile.flush()


ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
