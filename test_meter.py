import json
import os
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import meter


class Upstream(BaseHTTPRequestHandler):
    """Answers like an OpenAI endpoint and records the paths it was asked for."""
    seen = []

    def log_message(self, *a):
        pass

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
        Upstream.seen.append(self.path)
        body = json.dumps({"usage": {"prompt_tokens": 3, "completion_tokens": 2}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class MeterTests(unittest.TestCase):
    def setUp(self):
        Upstream.seen = []
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.up = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        threading.Thread(target=self.up.serve_forever, daemon=True).start()
        self.addCleanup(self.up.shutdown)
        self.dump = os.path.join(self.tmp.name, "dump")
        os.makedirs(self.dump)
        meter.Handler.upstream = f"http://127.0.0.1:{self.up.server_port}"
        meter.Handler.log_path = os.path.join(self.tmp.name, "meter.jsonl")
        meter.Handler.dump_dir = self.dump
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), meter.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.shutdown)

    def post(self, raw_path):
        import http.client
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=10)
        c.request("POST", raw_path, body=b"{}", headers={"Content-Type": "application/json"})
        r = c.getresponse()
        r.read()
        c.close()
        return r.status

    def test_forwards_agent_paths(self):
        for p in ("/run~a~0~ab12/v1/chat/completions", "/run/v1/messages",
                  "/run/v1beta/models/bench-model:streamGenerateContent?alt=sse"):
            self.assertEqual(self.post(p), 200, p)
        self.assertEqual(Upstream.seen, ["/v1/chat/completions", "/v1/messages",
                                         "/v1beta/models/bench-model:streamGenerateContent?alt=sse"])

    def test_refuses_paths_that_name_another_host(self):
        for p in ("/run//evil.example/v1/chat/completions", "/run/http://evil.example/x"):
            self.assertEqual(self.post(p), 400, p)
        self.assertEqual(Upstream.seen, [])

    def test_dump_names_stay_inside_the_dump_dir(self):
        self.assertEqual(self.post("/..%2F..%2Fescape/v1/chat/completions"), 200)
        for _ in range(50):  # the dump is written after the response is sent
            names = os.listdir(self.dump)
            if len(names) == 2:
                break
            time.sleep(0.05)
        self.assertTrue(names and all("/" not in n and not n.startswith(".") for n in names), names)
        self.assertEqual(sorted(os.listdir(self.tmp.name)), ["dump", "meter.jsonl"])

    def test_safe_label(self):
        self.assertEqual(meter.safe_label("chanto~swe-x~0~ab12"), "chanto~swe-x~0~ab12")
        self.assertEqual(meter.safe_label("../../etc"), "_.._etc")
        self.assertEqual(meter.safe_label(".."), "unlabelled")


if __name__ == "__main__":
    unittest.main()
