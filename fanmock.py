#!/usr/bin/env python3
"""The model for fanout.py. The agent's first request gets N calls to its
subagent tool at once. Each subagent reads a file, then finishes. Every reply
waits --delay seconds, so subagents overlap and the model's time is known.

Speaks OpenAI chat, OpenAI Responses and Anthropic Messages, streaming or not.
Logs each request; prints 'PORT <n>'."""
import argparse, http.server, json, re, socketserver, threading, time

import stressmock

LOCK = threading.Lock()
STATE = {"root": 0, "child": {}, "started": set(), "finished": set(), "max_live": 0}
ARGS = None
SUBAGENT = ("task", "agent", "spawn_agent", "spawn_subagent", "subagent", "delegate", "dispatch_agent", "new_task")
NAMESPACE = {}
CHILD = re.compile(r"FANOUT-CHILD-(\d+)")


def walk_tools(tools, out):
    for t in tools or []:
        if not isinstance(t, dict):
            continue
        if isinstance(t.get("tools"), list):  # A namespace of tools (Codex).
            walk_tools(t["tools"], out)
            for inner in t["tools"]:
                if isinstance(inner, dict) and inner.get("name"):
                    NAMESPACE[inner["name"]] = t.get("name")
            continue
        f = t.get("function") or t
        params = f.get("parameters") or f.get("input_schema") or f.get("parametersJsonSchema") or {}
        if f.get("name"):
            out.append((f["name"], params.get("properties") or {}, params.get("required") or []))
    return out


def all_tools(body):
    tools = list(body.get("tools") or [])
    for item in body.get("input") or []:  # Codex sends tools as an input item too.
        if isinstance(item, dict) and item.get("type") == "additional_tools":
            tools += item.get("tools") or []
    return walk_tools(tools, [])


def subagent_tool(body):
    tools = all_tools(body)
    for want in SUBAGENT:
        for tool in tools:
            if tool[0].lower() == want:
                return tool
    return None


def subagent_args(props, req, i):
    prompt = f"FANOUT-CHILD-{i}: read big.txt, then say done."
    args = {}
    for p in set(req) | set(props):
        pl, spec = p.lower(), props.get(p, {})
        if any(k in pl for k in ("prompt", "message", "task", "instruction", "input", "query")):
            args[p] = prompt
        elif "description" in pl or pl in ("name", "title"):
            args[p] = f"child {i}"
        elif "subagent_type" in pl or pl in ("agent", "agent_type", "subagent", "type", "mode"):
            enum = spec.get("enum")
            if enum:
                args[p] = enum[0]
            elif p in req or "subagent_type" in pl:
                args[p] = "general-purpose" if "subagent_type" in pl else "general"
        elif p in req:
            args[p] = {"boolean": False, "integer": 1, "number": 1}.get(spec.get("type"), "x")
    return args


def read_tool(body):
    """A read or shell call for this subagent, from the tools it was offered."""
    picked = stressmock.pick(body)
    if not picked:
        return None
    name, props, req, is_shell = picked
    args = {}
    for p in req or list(props)[:1]:
        pl = p.lower()
        if is_shell and any(k in pl for k in ("command", "cmd", "script")):
            args[p] = ["cat", "big.txt"] if props.get(p, {}).get("type") == "array" else "cat big.txt"
        elif any(k in pl for k in ("file", "path")):
            args[p] = "big.txt"
        elif p in req:
            args[p] = {"boolean": False, "integer": 1, "number": 1}.get(props.get(p, {}).get("type"), "t")
    return name, args


def decide(body):
    """(tool calls as [(name, args)], text) for this request."""
    text = json.dumps(body.get("messages") or body.get("input") or "")
    kids = CHILD.findall(text)
    fresh = "FANOUT-ROOT" in text
    # A request with no tools isn't the turn itself (a title, say).
    if not all_tools(body):
        return [], "A title"
    with LOCK:
        if kids and not (fresh and not STATE["started"]):
            kid = kids[0]
            n = STATE["child"].get(kid, 0)
            STATE["child"][kid] = n + 1
            if "FANOUT-ROOT" in text:
                # A parent's history holds its children's prompts: that's the root.
                pass
            else:
                STATE["started"].add(kid)
                if n == 0:
                    tool = read_tool(body)
                    if tool:
                        return [tool], ""
                STATE["finished"].add(kid)
                return [], f"child {kid} done"
        STATE["root"] += 1
        first = STATE["root"] == 1
    if first:
        sub = subagent_tool(body)
        if not sub:
            return [], "NO-SUBAGENT-TOOL"
        return [(sub[0], subagent_args(sub[1], sub[2], i)) for i in range(ARGS.agents)], ""
    # An agent that doesn't wait for its subagents by itself (Codex) would end
    # the run here: a real model takes its time, so give them time to finish.
    deadline = time.time() + ARGS.limit
    while time.time() < deadline:
        with LOCK:
            if len(STATE["finished"]) >= ARGS.agents:
                break
        time.sleep(0.02)
    return [], "all done"


def call_id(n, i):
    return f"call_{n}_{i}"


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def do_GET(self):
        self.send_json({"data": [], "models": []})

    def send_json(self, value):
        b = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def sse(self, chunks):
        b = "".join(chunks).encode()
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.send_header("content-length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("content-length", 0)))
        try:
            body = json.loads(raw)
        except ValueError:
            body = {}
        if "/count_tokens" in self.path:
            return self.send_json({"input_tokens": 1000})
        if stressmock.is_summary(body):
            calls, text = [], "A summary."
        else:
            calls, text = decide(body)
        time.sleep(ARGS.delay)
        with LOCK:
            n = STATE.setdefault("req", 0) + 1
            STATE["req"] = n
            with open(ARGS.log, "a") as f:
                f.write(json.dumps({"n": n, "t": time.time(), "path": self.path, "calls": [c[0] for c in calls],
                                    "text": text[:40], "tools": [t[0] for t in all_tools(body)] if n == 1 else None,
                                    "started": len(STATE["started"]), "finished": len(STATE["finished"])}) + "\n")
        try:
            if "/messages" in self.path:
                self.anthropic(n, calls, text, bool(body.get("stream")))
            elif "/responses" in self.path:
                self.openai_responses(n, calls, text)
            else:
                self.chat(n, calls, text, bool(body.get("stream")))
        except (BrokenPipeError, ConnectionResetError):
            pass

    def chat(self, n, calls, text, stream):
        usage = {"prompt_tokens": 100, "completion_tokens": 5, "total_tokens": 105}
        tool_calls = [{"index": i, "id": call_id(n, i), "type": "function",
                       "function": {"name": c[0], "arguments": json.dumps(c[1])}} for i, c in enumerate(calls)]
        finish = "tool_calls" if calls else "stop"
        base = {"id": f"c{n}", "created": int(time.time()), "model": "fake"}
        if not stream:
            message = {"role": "assistant", "content": text or None}
            if calls:
                message["tool_calls"] = tool_calls
            return self.send_json({**base, "object": "chat.completion", "usage": usage,
                                   "choices": [{"index": 0, "message": message, "finish_reason": finish}]})
        delta = {"role": "assistant", "content": text}
        if calls:
            delta["tool_calls"] = tool_calls
        ev = lambda d, f=None, **k: "data: " + json.dumps({**base, "object": "chat.completion.chunk", **k,
                                                           "choices": [{"index": 0, "delta": d, "finish_reason": f}]}) + "\n\n"
        self.sse([ev(delta), ev({}, finish, usage=usage), "data: [DONE]\n\n"])

    def openai_responses(self, n, calls, text):
        ev = lambda t, **k: f"event: {t}\ndata: " + json.dumps({"type": t, **k}) + "\n\n"
        output = [{"type": "function_call", "id": f"fc_{n}_{i}", "call_id": call_id(n, i), "status": "completed",
                   "name": c[0], "arguments": json.dumps(c[1]),
                   **({"namespace": NAMESPACE[c[0]]} if c[0] in NAMESPACE else {})} for i, c in enumerate(calls)]
        if text:
            output.append({"type": "message", "id": f"m{n}", "role": "assistant", "status": "completed",
                           "content": [{"type": "output_text", "text": text, "annotations": []}]})
        resp = {"id": f"r{n}", "object": "response", "status": "completed", "model": "fake", "output": output,
                "usage": {"input_tokens": 100, "output_tokens": 5, "total_tokens": 105,
                          "input_tokens_details": {"cached_tokens": 0}, "output_tokens_details": {"reasoning_tokens": 0}}}
        chunks = [ev("response.created", response={**resp, "status": "in_progress", "output": []})]
        for i, item in enumerate(output):
            chunks += [ev("response.output_item.added", output_index=i, item=item),
                       ev("response.output_item.done", output_index=i, item=item)]
        self.sse(chunks + [ev("response.completed", response=resp)])

    def anthropic(self, n, calls, text, stream):
        blocks = ([{"type": "text", "text": text}] if text else []) + [
            {"type": "tool_use", "id": call_id(n, i), "name": c[0], "input": c[1]} for i, c in enumerate(calls)]
        stop = "tool_use" if calls else "end_turn"
        usage = {"input_tokens": 100, "output_tokens": 5}
        msg = {"id": f"m{n}", "type": "message", "role": "assistant", "model": "fake", "stop_sequence": None}
        if not stream:
            return self.send_json({**msg, "content": blocks, "stop_reason": stop, "usage": usage})
        ev = lambda t, **k: f"event: {t}\ndata: " + json.dumps({"type": t, **k}) + "\n\n"
        chunks = [ev("message_start", message={**msg, "content": [], "stop_reason": None, "usage": usage})]
        for i, b in enumerate(blocks):
            start = {**b, "input": {}} if b["type"] == "tool_use" else {"type": "text", "text": ""}
            chunks.append(ev("content_block_start", index=i, content_block=start))
            delta = {"type": "input_json_delta", "partial_json": json.dumps(b["input"])} if b["type"] == "tool_use" \
                else {"type": "text_delta", "text": b["text"]}
            chunks += [ev("content_block_delta", index=i, delta=delta), ev("content_block_stop", index=i)]
        chunks += [ev("message_delta", delta={"stop_reason": stop, "stop_sequence": None}, usage={"output_tokens": 5}),
                   ev("message_stop")]
        self.sse(chunks)


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    request_queue_size = 512


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", type=int, required=True)
    ap.add_argument("--delay", type=float, default=0.5)
    ap.add_argument("--log", required=True)
    ap.add_argument("--limit", type=float, default=300)
    ARGS = ap.parse_args()
    server = Server(("127.0.0.1", 0), Handler)
    print("PORT", server.server_address[1], flush=True)
    server.serve_forever()
