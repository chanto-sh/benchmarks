"""Runner regressions; opt into real macOS SBPL checks with BENCH_SANDBOX_SMOKE=1."""
import contextlib
import io
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import run


class RunnerTests(unittest.TestCase):
    def test_redact_hides_home_and_user(self):
        home, user = str(Path.home()), __import__("getpass").getuser()
        text = f"{home}/x/y and /tmp/pytest-of-{user}/p0"
        self.assertEqual(run.redact(text), "~/x/y and /tmp/pytest-of-user/p0")
        self.assertEqual(run.redact(text.encode()), b"~/x/y and /tmp/pytest-of-user/p0")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name, value in {"WORK": self.root / "work", "TASKS": self.root / "tasks",
                            "RESULTS": self.root / "results", "API": None, "METER": None,
                            "OFFLINE": False, "CHANTO_EFFORT": None}.items():
            p = patch.object(run, name, value)
            p.start()
            self.addCleanup(p.stop)

    def task(self, check="exit 0"):
        task = run.TASKS / "tiny"
        (task / "files").mkdir(parents=True)
        (task / "files/README.md").write_text("Fixture repository\n")
        (task / "prompt.txt").write_text("Do nothing")
        (task / "check.sh").write_text(check)

    def test_profile_protects_writes_and_escapes_paths(self):
        wd = run.WORK / 'space "quote" \\ slash'
        home = run.WORK / ".homes/chanto"
        binary = run.CHANTO_REPO / "target/release/chanto"
        profile = run.offline_profile(wd, home, binary)
        # Neither this repository (hidden tests, past runs) nor the Chanto sources.
        for hidden in (run.ROOT, run.CHANTO_REPO):
            self.assertIn(f'(deny file-read-data file-write* (subpath {json.dumps(str(hidden))}))', profile)
        for path in (wd, home):
            self.assertIn(f'(allow file-read* file-read-data file-write* (subpath {json.dumps(str(path.resolve()))}))', profile)
        self.assertIn(f'(allow file-read* file-read-data (literal {json.dumps(str(binary.resolve()))}))', profile)
        self.assertNotIn('(allow file-write* (literal', profile)
        # Installed packages and other bench data could hold the upstream fix.
        self.assertIn('(deny file-read-data file-write* (regex #"/(site|dist)-packages(/|$)"))', profile)
        # A copy of this repository under another name hides the same tasks and runs.
        names = run.CHECKOUT_NAMES
        self.assertIn(f'(deny file-read-data file-write* (regex #"/({names})/(tasks|results)(/|$)"))', profile)
        self.assertIn(f'(deny file-read-data file-write* (regex #"/({names})/swebench-[^/]*\\.json$"))', profile)
        self.assertIn(f'(deny file-read-data file-write* (subpath {json.dumps(str((Path.home() / ".local/share/chanto-bench").resolve()))}))', profile)
        self.assertLess(profile.index(f'/({run.CHECKOUT_NAMES})/(tasks|results)'), profile.index('(allow file-read* file-read-data file-write*'))
        self.assertLess(profile.index('site|dist'), profile.index('(allow file-read* file-read-data file-write*'))
        self.assertLess(profile.index('(deny file-read-data'), profile.index('(allow file-read* file-read-data file-write*'))

    def test_public_benchmark_tasks_keep_system_packages_readable(self):
        wd, home = run.WORK / "wd", run.WORK / ".homes/chanto"
        keep = run.offline_profile(wd, home, keep_site_packages=True)
        hide = run.offline_profile(wd, home)
        allow = '(allow file-read* file-read-data (regex #"/(site|dist)-packages(/|$)"))'
        deny = '(deny file-read-data file-write* (regex #"/(site|dist)-packages(/|$)"))'
        self.assertIn(allow, keep)
        self.assertNotIn(deny, keep)
        self.assertIn(deny, hide)
        self.assertNotIn(allow, hide)

    def test_config_restored_on_success_and_failure(self):
        config = run.home("chanto") / "config.toml"
        for previous in (None, b'# original\n[sandbox]\nenabled = true\n'):
            for fail in (False, True):
                with self.subTest(previous=previous, fail=fail), patch.object(run.sys, "platform", "darwin"):
                    if previous is None:
                        config.unlink(missing_ok=True)
                    else:
                        config.write_bytes(previous)
                    try:
                        with run.offline("chanto-verify", [str(run.CHANTO_BIN)], run.WORK / "task") as cmd:
                            self.assertEqual(cmd[0], "sandbox-exec")
                            self.assertEqual(config.read_text(), "[sandbox]\nenabled = false\n")
                            if fail:
                                raise OSError("launch failed")
                    except OSError:
                        self.assertTrue(fail)
                    if previous is None:
                        self.assertFalse(config.exists())
                    else:
                        self.assertEqual(config.read_bytes(), previous)

    def test_config_restored_after_invocation_timeout_or_launch_error(self):
        self.task()
        config = run.home("chanto") / "config.toml"
        previous = b"# preserved\n[sandbox]\nenabled = true\n"
        popen = subprocess.Popen
        for launch_error in (False, True):
            config.write_bytes(previous)

            def launch(cmd, *args, **kwargs):
                if cmd[0] == "sandbox-exec":
                    self.assertEqual(config.read_text(), "[sandbox]\nenabled = false\n")
                    if launch_error:
                        raise OSError("launch failed")
                    cmd = cmd[3:]  # Exercise lifetime management without a real sandbox.
                return popen(cmd, *args, **kwargs)

            with patch.object(run, "OFFLINE", True), patch.object(run.sys, "platform", "darwin"), patch.object(run, "agent_cmd", return_value=([sys.executable, "-c", "import time; time.sleep(10)"], {})), patch.object(run.subprocess, "Popen", side_effect=launch):
                if launch_error:
                    with self.assertRaisesRegex(OSError, "launch failed"):
                        run.run_task("chanto", "tiny", "model", 100, 0.1, 0)
                else:
                    result = run.run_task("chanto", "tiny", "model", 100, 0.1, 0)
                    self.assertTrue(result["timed_out"])
            self.assertEqual(config.read_bytes(), previous)

    def test_unsupported_platform_before_setup(self):
        # Linux without bubblewrap and socat can't run offline.
        no_tools = patch.object(run.shutil, "which", return_value=None)
        no_tools.start()
        self.addCleanup(no_tools.stop)
        with patch.object(run, "OFFLINE", True), patch.object(run.sys, "platform", "linux"), patch.object(run, "prepare_task") as setup:
            with self.assertRaisesRegex(SystemExit, "macOS"):
                run.run_task("chanto", "missing", "model", 100, 1, 0)
            setup.assert_not_called()
        with patch.object(run.sys, "platform", "linux"), patch.object(sys, "argv", ["run.py", "--offline", "--sanity"]), patch.object(run, "prepare_task") as setup:
            with self.assertRaisesRegex(SystemExit, "macOS"):
                run.main()
            setup.assert_not_called()

    def test_check_exit_and_timeout(self):
        result = run.run_check([sys.executable, "-c", "import sys; print('out'); print('err', file=sys.stderr); sys.exit(3)"], self.root, os.environ)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (3, "out\n", "err\n"))
        result = run.run_check([sys.executable, "-c", "import time; print('started', flush=True); time.sleep(10)"], self.root, os.environ, timeout=0.1)
        self.assertEqual(result.returncode, 124)
        self.assertIn("started", result.stdout)
        self.assertIn("timed out after 0.1s", result.stderr)

    def child_command(self, marker, wait=False):
        child = f"import time; from pathlib import Path; time.sleep(0.5); Path({str(marker)!r}).write_text('survived')"
        parent = f"import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', {child!r}], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
        return [sys.executable, "-c", parent + ("time.sleep(10)" if wait else "")]

    def test_check_cleans_children_on_normal_exit_and_timeout(self):
        for wait in (False, True):
            marker = self.root / f"check-child-{wait}"
            result = run.run_check(self.child_command(marker, wait), self.root, os.environ, timeout=0.1 if wait else 5)
            self.assertEqual(result.returncode, 124 if wait else 0)
            time.sleep(0.6)
            self.assertFalse(marker.exists())

    def test_agent_cleans_children_on_normal_exit_and_timeout(self):
        self.task()
        for wait in (False, True):
            marker = self.root / f"agent-child-{wait}"
            with patch.object(run, "agent_cmd", return_value=(self.child_command(marker, wait), {})):
                result = run.run_task("fake", "tiny", "model", 100, 0.1 if wait else 5, int(wait))
            self.assertEqual(result["timed_out"], wait)
            self.assertEqual(result["exit_code"], -1 if wait else 0)
            time.sleep(0.6)
            self.assertFalse(marker.exists())

    def test_reap_gives_up_on_a_process_that_will_not_die(self):
        class Stuck:
            pid = 12345
            killed = False

            def poll(self):
                return None

            def kill(self):
                self.killed = True

            def wait(self, timeout=None):
                if timeout is None:
                    time.sleep(60)  # what the old unbounded wait() would have done
                raise subprocess.TimeoutExpired("stuck", timeout)

        p = Stuck()
        with patch.object(run.os, "killpg"):
            t = time.time()
            run.reap(p, grace=0.05)
        self.assertLess(time.time() - t, 5.0, "reap waited unboundedly for a process that will not die")
        self.assertTrue(p.killed, "reap should escalate to kill()")

    def test_cleanup_delay_is_not_billed_to_the_task(self):
        # A process that takes ages to reap (stuck in a kernel call) must not
        # inflate the recorded seconds; the clock stops at the deadline.
        self.task()

        def slow_reap(p, grace=10):
            run.kill_process_group(p)
            p.wait()
            time.sleep(1.5)

        with patch.object(run, "agent_cmd", return_value=([sys.executable, "-c", "import time; time.sleep(3)"], {})), \
             patch.object(run, "reap", slow_reap):
            result = run.run_task("fake", "tiny", "model", 100, 0.1, 0)
        self.assertTrue(result["timed_out"])
        self.assertLess(result["seconds"], 1.0, "cleanup time leaked into the recorded seconds")

    def test_tiers_select_and_estimate(self):
        for name in ("poly-a", "trap-b", "swe-c", "custom-d", "trap-imp-e", "coding-f", "math-g",
                     "physics-h", "data-i", "analysis-j", "nontrad-k"):
            (run.TASKS / name).mkdir(parents=True)
        self.assertEqual(run.select_tasks(["core"], None), ["poly-a", "trap-b"])
        self.assertEqual(run.select_tasks(["hard", "medium"], None), ["custom-d", "swe-c"])
        self.assertEqual(run.select_tasks(run.TIERS, "poly-*,swe-*"), ["poly-a", "swe-c"])
        self.assertEqual(run.select_tasks(["beyond"], None), ["coding-f", "math-g", "physics-h", "trap-imp-e"])
        self.assertEqual(run.select_tasks(["showcase"], None), ["analysis-j", "data-i", "nontrad-k"])
        # The default run is the coding suite; showcase is opt-in.
        self.assertNotIn("showcase", run.CODING_TIERS)
        self.assertEqual(set(run.TIERS) - set(run.CODING_TIERS), {"showcase"})
        for name in ("trap-imp-e", "coding-f", "math-g", "physics-h", "data-i", "analysis-j", "nontrad-k"):
            (run.TASKS / name).rmdir()
        ref = self.root / "ref.json"
        ref.write_text(json.dumps({"results": [
            {"agent": "chanto", "task": "poly-a", "seconds": 10, "usage": {"input": 1000, "output": 100, "cached": 400}},
            {"agent": "other", "task": "swe-c", "seconds": 100, "usage": {"input": 5000, "output": 500}},
        ]}))
        counts, rows = run.estimate(["chanto"], ["core", "hard"], 2, [str(ref)])
        self.assertEqual(counts, {"core": 2, "hard": 1})
        agent, tin, tout, tcache, secs = rows[0]
        # core: own history (2 tasks x 2 reps); hard: falls back to the other agent's.
        self.assertEqual((agent, tin, tout, tcache), ("chanto", 1000 * 4 + 5000 * 2, 100 * 4 + 500 * 2, 400 * 4))
        # Cache hits are billed at their own rate, not the input rate:
        # 12400 uncached in @$1 + 1600 cache hits @$0.25 + 1400 out @$2, per M tok.
        self.assertAlmostEqual(run.cost_of(tin, tout, tcache, (1e-6, 0.25e-6, 2e-6)), 0.0156, places=6)
        # Every model's price is an (off-peak, peak) pair of (in, cache-hit, out) triples.
        for off, peak in run.PRICES.values():
            self.assertEqual(len(off), 3)
            self.assertEqual(len(peak), 3)
        self.assertEqual(secs, 10 * 4 + 100 * 2)
        self.assertEqual(run.hms(90061), "25:01:01")

    def test_evalplus_tasks_join_the_core_tier(self):
        for name in ("humaneval-0", "mbpp-2"):
            (run.TASKS / name).mkdir(parents=True)
        self.assertEqual(run.select_tasks(["core"], None), ["humaneval-0", "mbpp-2"])
        self.assertEqual(run.select_tasks(["hard"], "humaneval-*"), [])

    def test_data_science_and_finance_tasks_land_in_their_tiers(self):
        for name in ("ds1000-7", "finqa-AAPL_2004_page_68_pdf-1"):
            (run.TASKS / name).mkdir(parents=True)
        self.assertEqual(run.select_tasks(["medium"], None), ["ds1000-7"])
        self.assertEqual(run.select_tasks(["showcase"], None),
                         ["finqa-AAPL_2004_page_68_pdf-1"])
        self.assertEqual(run.select_tasks(["core", "hard", "beyond"], None), [])

    def test_evidence_keeps_the_change_transcript_and_grader_output(self):
        wd = self.root / "ws"
        wd.mkdir()
        git = lambda *a: subprocess.run(["git", *a], cwd=wd, check=True, capture_output=True)
        (wd / "a.py").write_text("x = 1\n")
        git("init", "-q"); git("add", "-A"); git("-c", "user.email=b@b", "-c", "user.name=b", "commit", "-qm", "init")
        (wd / "a.py").write_text("x = 2\n")
        (wd / "new.py").write_text("y = 3\n")
        patch = run.workspace_diff(wd)
        self.assertIn(b"+x = 2", patch)
        self.assertIn(b"+y = 3", patch)
        # The repo's own index is untouched (the grader may rely on it).
        status = subprocess.run(["git", "status", "--porcelain"], cwd=wd, capture_output=True, text=True).stdout
        self.assertIn("?? new.py", status)
        out = self.root / "t.out"
        out.write_text("agent transcript")
        chk = subprocess.CompletedProcess([], 1, stdout="1 failed", stderr="")
        run.ARTIFACTS = self.root / "evidence"
        try:
            ev = run.keep_evidence("chanto", "tiny", 0, out, patch, chk)
        finally:
            run.ARTIFACTS = None
        self.assertEqual((self.root / "evidence" / "chanto~tiny~0.out").read_text(), "agent transcript")
        self.assertIn("1 failed", (self.root / "evidence" / "chanto~tiny~0.check.txt").read_text())
        self.assertEqual(ev["patch"]["sha256"], hashlib.sha256(patch).hexdigest())
        # The agent's own session files written during the run are kept too.
        agent_home = self.root / "home"
        (agent_home / "sessions/p").mkdir(parents=True)
        old_session = agent_home / "sessions/p/old.json"
        old_session.write_text("{}")
        os.utime(old_session, (1, 1))
        (agent_home / "sessions/p/new.json").write_text('{"messages": []}')
        (agent_home / "projects").mkdir()
        (agent_home / "projects/run.jsonl").write_text("{}\n")
        (agent_home / "settings.json").write_text("{}")
        found = run.session_files(agent_home, time.time() - 60)
        self.assertEqual(sorted(p.name for p in found), ["new.json", "run.jsonl"])

    def test_leak_detection_attributes_evidence_to_the_cell(self):
        out = self.root / "a.out"
        out.write_text("$ find /repo/bench/tasks/tiny/pristine/test.py\n")
        self.assertTrue(run.test_leak("tiny", 0, out))
        # A transcript that never mentions the hidden tests is clean.
        out.write_text("$ cat solution.py\n")
        self.assertFalse(run.test_leak("tiny", 0, out))
        # Some agents append every session to one log: another cell's line that
        # names the tests is not this cell's leak.
        log = self.root / "events.jsonl"
        log.write_text('{"root": "/w/tiny-1", "cmd": "cat tasks/tiny/pristine/test.py"}\n'
                       '{"root": "/w/tiny-0", "cmd": "cat solution.py"}\n')
        self.assertFalse(run.test_leak("tiny", 0, out, [log]))
        self.assertTrue(run.test_leak("tiny", 1, out, [log]))

    def test_report_pairs_agents_and_tests_significance(self):
        self.assertAlmostEqual(run.sign_test(0, 0), 1.0)
        self.assertAlmostEqual(run.sign_test(5, 0), 0.0625)  # 2 * (1/2)^5
        self.assertAlmostEqual(run.sign_test(3, 3), 1.0)
        results = [
            {"agent": "chanto", "task": t, "rep": 0, "passed": p, "seconds": 1, "timed_out": False}
            for t, p in [("a", True), ("b", True), ("c", False)]
        ] + [
            {"agent": "other", "task": t, "rep": 0, "passed": p, "seconds": 1, "timed_out": False}
            for t, p in [("a", False), ("b", True), ("c", True)]
        ]
        self.assertEqual(run.paired(results, "chanto"), [("other", 3, 1, 1, 1.0)])
        f = self.root / "r.json"
        f.write_text(json.dumps({"model": "m", "ctx": 1, "meta": {"upstream_model": "up/model"}, "results": results + results[:1]}))
        text = run.report([str(f), str(f)])
        self.assertIn("`up/model` (as `m`)", text)
        self.assertIn("| other | 3 | 1 | 1 | 1.00 (not significant) |", text)
        self.assertIn("**2/3**", text)  # a run listed twice counts once
        # Totals only count tasks every agent ran.
        extra = results + [{"agent": "chanto", "task": "d", "rep": 0, "passed": True, "seconds": 1, "timed_out": False}]
        f.write_text(json.dumps({"model": "m", "ctx": 1, "results": extra}))
        text = run.report([str(f)])
        self.assertIn("Totals cover the 3 tasks every agent ran; 1 runs", text)
        self.assertIn("**2/3**", text)
        # Showcase tasks get their own totals and stay out of the coding score and pairing.
        show = results + [{"agent": a, "task": "data-x", "rep": 0, "passed": True, "seconds": 1, "timed_out": False}
                          for a in ("chanto", "other")]
        f.write_text(json.dumps({"model": "m", "ctx": 1, "results": show}))
        text = run.report([str(f)])
        head, tail = text.split("Showcase tier (1 tasks")
        self.assertIn("**2/3**", head)
        self.assertIn("**1/1**", tail.split("| task |")[0])
        self.assertIn("| other | 3 | 1 | 1 | 1.00 (not significant) |", text)

    def test_completion_status_reads_the_agent_own_signal(self):
        out = self.root / "a.out"
        # chanto and claude end a print-mode turn with a `result` JSON carrying
        # is_error; that, not the exit code, is the completion signal.
        out.write_text('{"type":"result","is_error":false}\n')
        self.assertEqual(run.completion_status("chanto", False, out), (True, False))
        self.assertEqual(run.completion_status("chanto-verify", False, out), (True, False))
        self.assertEqual(run.completion_status("claude", False, out), (True, False))
        out.write_text('{"type":"result","is_error":true,"result":"boom"}\n')
        self.assertEqual(run.completion_status("chanto", False, out), (False, True))
        # Claude's warning line starts with "[" so it isn't mistaken for the result.
        out.write_text('{"type":"result","is_error":false}\n[claude-code:unrecognized_model] {"model":"m"}\n')
        self.assertEqual(run.completion_status("claude", False, out), (True, False))
        # forge reports failure in-band and exits 0 regardless.
        out.write_text("\u25cf [09:34:05] ERROR: Device not configured (os error 6)\n")
        self.assertEqual(run.completion_status("forge", False, out), (False, True))
        out.write_text("Made the change and ran the tests.\n")
        self.assertEqual(run.completion_status("forge", False, out), (True, False))
        # An agent that prints no signal is unknown — not assumed to be finished,
        # and not assumed to have errored (the exit code can't tell us either).
        out.write_text("done\n")
        self.assertEqual(run.completion_status("aider", False, out), (None, None))
        # A run killed at the deadline never got to report either way.
        self.assertEqual(run.completion_status("chanto", True, out), (None, None))

    def test_report_separates_claims_from_the_exit_code_proxy(self):
        def mk(agent, claimed, passed=False, fd=False):
            return {"agent": agent, "task": "a", "rep": 0, "passed": passed, "seconds": 1,
                    "timed_out": False, "claimed_done": claimed, "false_done": fd,
                    "errored": claimed is False, "clean_exit_fail": fd}
        results = [mk("chanto", True, fd=True), mk("aider", None, fd=True), mk("forge", False)]
        f = self.root / "r.json"
        f.write_text(json.dumps({"model": "m", "ctx": 1, "results": results}))
        text = run.report([str(f)])
        row = lambda a: next(l for l in text.splitlines() if l.startswith(f"| {a} |")).split("|")
        # chanto really claimed success and failed; aider prints no signal, so
        # its claim is "—" and the exit-code proxy shows beside it; forge errored.
        self.assertEqual(row("chanto")[4].strip(), "1")
        self.assertEqual(row("chanto")[5].strip(), "0")
        self.assertEqual(row("aider")[4].strip(), "—")
        self.assertEqual(row("aider")[5].strip(), "—")
        self.assertEqual(row("aider")[6].strip(), "1")
        self.assertEqual(row("forge")[4].strip(), "0")
        self.assertEqual(row("forge")[5].strip(), "1")

    def test_validate_tasks_grades_overlays(self):
        import validate_tasks
        task = run.TASKS / "math-tiny"
        (task / "files").mkdir(parents=True)
        (task / "files/old.txt").write_text("x")
        (task / "check.sh").write_text('[ "$(cat answer.txt)" = 42 ] && [ ! -e old.txt ] && grep -q done "$OUTPUT_FILE"\n')
        (task / "ref").mkdir()
        (task / "ref/answer.txt").write_text("42")
        (task / "ref/_OUTPUT.txt").write_text("done")
        (task / "ref/_DELETE").write_text("old.txt")
        r, _ = validate_tasks.grade("math-tiny", None, self.root / "v0")
        self.assertNotEqual(r.returncode, 0)
        r, _ = validate_tasks.grade("math-tiny", task / "ref", self.root / "v1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse((self.root / "v1/math-tiny/_OUTPUT.txt").exists())

    def test_offline_metadata_in_both_result_paths(self):
        self.task()
        for offline in (False, True):
            for budget in (False, True):
                with self.subTest(offline=offline, budget=budget):
                    for f in run.RESULTS.glob("*.json"):
                        f.unlink()
                    out = run.WORK / "chanto/tiny-0.out"
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text("budget exhausted" if budget else "done")
                    result = {"passed": not budget, "seconds": 0, "timed_out": False, "agent": "chanto"}
                    argv = ["run.py", "--tasks", "tiny"] + (["--offline"] if offline else [])
                    with patch.object(sys, "argv", argv), patch.object(run.sys, "platform", "darwin"), patch.object(run, "run_task", return_value=result), contextlib.redirect_stdout(io.StringIO()):
                        if budget:
                            with self.assertRaises(SystemExit):
                                run.main()
                        else:
                            run.main()
                    data = json.loads(next(run.RESULTS.glob("*.json")).read_text())
                    self.assertEqual(data["offline"], offline)
                    self.assertEqual(data.get("aborted"), "out of budget" if budget else None)
                    self.assertEqual(len(data["results"]), 0 if budget else 1)
                    # Each result file says exactly what ran.
                    self.assertIn("chanto", data["meta"]["agent_versions"])
                    self.assertIn("tiny", data["meta"]["tasks"])

    def test_agents_resolve_to_the_benchmarks_own_installs(self):
        # A pinned copy in the benchmark's prefix wins over whatever is on PATH;
        # with none, the bare name (PATH) is the fallback.
        with tempfile.TemporaryDirectory() as d:
            npm, bins, uv = Path(d) / "npm", Path(d) / "bin", Path(d) / "uv"
            (npm).mkdir(); (bins).mkdir(); (uv / "aider-chat" / "bin").mkdir(parents=True)
            (npm / "claude").touch(); (bins / "goose").touch(); (uv / "aider-chat" / "bin" / "aider").touch()
            with patch.object(run, "NPM_BIN", npm), patch.object(run, "BIN_DIR", bins), patch.object(run, "UV_TOOLS", uv):
                self.assertEqual(run.agent_exe("claude"), str(npm / "claude"))
                self.assertEqual(run.agent_exe("goose"), str(bins / "goose"))
                self.assertEqual(run.agent_exe("aider"), str(uv / "aider-chat" / "bin" / "aider"))
                self.assertEqual(run.agent_exe("opencode"), "opencode")

    def test_continue_and_openhands_run_headless_against_the_proxy(self):
        wd = self.root / "wd"
        with patch.object(run, "API", "http://localhost:4000"):
            cmd, env = run.agent_cmd("cn", "m", "do it", 8192, wd)
            self.assertEqual(cmd[1:4], ["-p", "--auto", "--config"])
            cfg = json.loads(Path(cmd[4]).read_text())  # YAML, written as JSON
            self.assertEqual(cfg["models"][0]["apiBase"], "http://localhost:4000/v1")
            self.assertEqual(cfg["models"][0]["apiKey"], run.API_KEY)
            # Its own HOME: Continue also reads ~/.claude/settings.json.
            self.assertEqual(env["HOME"], str(run.home("cn")))
            self.assertEqual(env["CONTINUE_CLI_ENABLE_TELEMETRY"], "0")

            cmd, env = run.agent_cmd("openhands", "m", "do it", 8192, wd)
            self.assertEqual(cmd[:3], [run.agent_exe("openhands"), "--headless", "--override-with-envs"])
            self.assertEqual(cmd[-2:], ["-t", "do it"])
            self.assertEqual((env["LLM_MODEL"], env["LLM_BASE_URL"], env["HOME"]),
                             ("openai/m", "http://localhost:4000/v1", str(run.home("openhands"))))
        self.assertIn("cn", run.VERSION_CMDS)
        self.assertIn("openhands", run.VERSION_CMDS)

    def test_overhead_mock_fills_closed_set_arguments(self):
        import stressmock
        # OpenHands' terminal tool requires a security_risk from a fixed list.
        props = {"command": {"type": "string"},
                 "security_risk": {"type": "string", "enum": ["UNKNOWN", "LOW", "MEDIUM", "HIGH"]}}
        args = stressmock.args_for(props, ["command", "security_risk"], 3, True)
        self.assertEqual(args, {"command": "cat f3.txt", "security_risk": "LOW"})
        args = stressmock.args_for({"mode": {"type": "string", "enum": ["view", "create"]}}, ["mode"], 1, False)
        self.assertEqual(args, {"mode": "view"})

    def test_overhead_mock_ends_runs_only_through_real_finish_tools(self):
        import stressmock
        tool = lambda name: {"name": name, "input_schema": {"type": "object", "properties": {}}}
        # Claude Code's ExitPlanMode isn't a finish tool; calling it every turn
        # once the budget is spent kept Claude Code running forever.
        self.assertIsNone(stressmock.pick_terminal({"tools": [tool("Read"), tool("ExitPlanMode"), tool("TaskStop")]}))
        self.assertEqual(stressmock.pick_terminal({"tools": [tool("Read"), tool("submit_and_exit")]})[0], "submit_and_exit")
        self.assertEqual(stressmock.pick_terminal({"tools": [tool("Exit")]})[0], "Exit")

    def test_optimization_variants_set_flags_and_keep_the_baseline(self):
        wd = self.root / "wd"
        for api in (None, "http://localhost:4000"):
            with self.subTest(api=api), patch.object(run, "API", api):
                base, base_env = run.agent_cmd("chanto", "m", "do it", 8192, wd)
                self.assertEqual(base_env["CHANTO_OPTIMIZE"], "none")
                self.assertNotIn("--effort", base)
                for agent, flags in [("chanto+concise", "concise"),
                                     ("chanto+quiet", "quiet"), ("chanto+provenance", "provenance"),
                                     ("chanto+all", "concise,quiet,provenance"),
                                     ("chanto+concise+provenance", "concise,provenance"), ("chanto+quiet+concise", "quiet,concise")]:
                    cmd, env = run.agent_cmd(agent, "m", "do it", 8192, wd)
                    self.assertEqual(env["CHANTO_OPTIMIZE"], flags, agent)
                    # Otherwise the same command as plain chanto.
                    self.assertEqual(cmd, base, agent)
                    self.assertEqual(env["CHANTO_HOME"], base_env["CHANTO_HOME"])
                with patch.object(run, "CHANTO_EFFORT", "high"):
                    for agent in ("chanto", "chanto+quiet", "chanto-verify"):
                        cmd, _ = run.agent_cmd(agent, "m", "do it", 8192, wd)
                        self.assertEqual(cmd[cmd.index("--effort") + 1], "high", agent)
        for bad in ("chanto+fast", "chanto+", "chanto+concise+concise", "chanto+quiet+quiet", "chanto+all+quiet"):
            with self.assertRaises(SystemExit):
                run.chanto_optimizations(bad)
        self.assertEqual(run.chanto_optimizations("chanto-verify"), [])

    def test_optimization_variants_recorded_in_results_and_meta(self):
        self.task()
        def fake_run(agent, *a, **k):
            out = run.WORK / agent / "tiny-0.out"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text("done")
            return {"passed": True, "seconds": 0, "timed_out": False, "agent": agent, "task": "tiny",
                    "optimize": [run.OPTIMIZE_FLAGS[n] for n in run.chanto_optimizations(agent)]}
        argv = ["run.py", "--tasks", "tiny", "--agents", "chanto,chanto+all,chanto+concise,chanto+quiet,chanto+provenance", "--chanto-effort", "medium"]
        with patch.object(sys, "argv", argv), patch.object(run, "run_task", side_effect=fake_run), contextlib.redirect_stdout(io.StringIO()):
            run.main()
        data = json.loads(next(run.RESULTS.glob("*.json")).read_text())
        all_flags = ["concise_prose", "quiet", "provenance"]
        self.assertEqual(data["meta"]["chanto_optimize"], {"chanto": [], "chanto+all": all_flags,
                                                            "chanto+concise": ["concise_prose"], "chanto+quiet": ["quiet"],
                                                            "chanto+provenance": ["provenance"]})
        self.assertEqual(data["meta"]["chanto_effort"], "medium")
        self.assertEqual({r["agent"]: r["optimize"] for r in data["results"]},
                         {"chanto": [], "chanto+all": all_flags, "chanto+concise": ["concise_prose"],
                          "chanto+quiet": ["quiet"], "chanto+provenance": ["provenance"]})
        with patch.object(sys, "argv", ["run.py", "--tasks", "tiny", "--agents", "chanto+nope"]), self.assertRaises(SystemExit):
            run.main()

    @unittest.skipUnless(sys.platform == "darwin" and os.environ.get("BENCH_SANDBOX_SMOKE") == "1", "opt-in macOS sandbox smoke")
    def test_macos_sandbox_smoke(self):
        hidden = self.root / 'protected "quote" \\ slash'
        hidden.mkdir()
        wd = hidden / "work/current"
        home = hidden / "work/.homes/chanto"
        wd.mkdir(parents=True)
        home.mkdir(parents=True)
        for d in (wd / ".venv/lib/site-packages", hidden.parent / "site-packages"):
            d.mkdir(parents=True, exist_ok=True)
            (d / "mod.py").write_text("ok")
        secret = hidden / "grading-input"
        secret.write_text("original")
        binary = hidden / "binary"
        # The Chanto sources are hidden as well as this repository.
        (hidden / "chanto").mkdir()
        sibling = hidden / "chanto" / "main.rs"
        # A script run with sh, not a copy of /bin/echo: macOS 26 kills copied
        # system binaries, and exec of a new unsigned script hangs in a sandbox.
        binary.write_text('#!/bin/sh\necho "$1"\n')
        binary.chmod(0o755)
        sibling.write_text("hidden")
        hidden, wd, home = hidden.resolve(), wd.resolve(), home.resolve()
        with patch.object(run, "ROOT", hidden), patch.object(run, "CHANTO_REPO", hidden / "chanto"), \
                patch.object(run, "WORK", hidden / "work"):
            profile = run.offline_profile(wd, home, binary)
        script = '''
import pathlib, socket, subprocess, sys
secret, sibling, binary, wd, home, port = sys.argv[1:]
import os
assert os.getcwd() == wd, os.getcwd()
# The task's own venv is readable; packages installed elsewhere aren't.
assert (pathlib.Path(wd) / ".venv/lib/site-packages/mod.py").read_text() == "ok"
try:
    (pathlib.Path(wd).parents[2] / "site-packages/mod.py").read_text()
except PermissionError:
    pass
else:
    raise AssertionError("outside site-packages readable")
for path in (secret, sibling):
    for operation in (lambda: pathlib.Path(path).read_text(), lambda: pathlib.Path(path).write_text("tampered")):
        try:
            operation()
        except PermissionError:
            pass
        else:
            raise AssertionError("protected access succeeded: " + path)
for path in (wd, home):
    p = pathlib.Path(path) / "allowed"
    p.write_text("ok")
    assert p.read_text() == "ok"
assert subprocess.check_output(["/bin/sh", binary, "ok"]).strip() == b"ok"
try:
    pathlib.Path(binary).write_text("tampered")
except PermissionError:
    pass
else:
    raise AssertionError("binary writable")
with socket.create_connection(("127.0.0.1", int(port)), timeout=2):
    pass
try:
    socket.create_connection(("1.1.1.1", 443), timeout=2)
except PermissionError:
    pass
else:
    raise AssertionError("external connection not denied")
'''
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            result = subprocess.run(["sandbox-exec", "-p", profile, sys.executable, "-c", script,
                                     str(secret), str(sibling), str(binary), str(wd), str(home), str(listener.getsockname()[1])],
                                    capture_output=True, text=True, timeout=10, cwd=wd)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(secret.read_text(), "original")


    @unittest.skipUnless(sys.platform.startswith("linux") and os.environ.get("BENCH_SANDBOX_SMOKE") == "1", "opt-in Linux sandbox smoke (needs bwrap, socat)")
    def test_linux_sandbox_smoke(self):
        import site
        hidden = self.root / "protected"
        wd = hidden / "work/current"
        home = hidden / "work/.homes/chanto"
        wd.mkdir(parents=True)
        home.mkdir(parents=True)
        secret = hidden / "grading-input"
        secret.write_text("original")
        # The Chanto sources are hidden as well as this repository.
        (hidden / "chanto").mkdir()
        sibling = hidden / "chanto" / "main.rs"
        sibling.write_text("hidden")
        binary = hidden / "binary"
        binary.write_text('#!/bin/sh\necho "$1"\n')
        binary.chmod(0o755)
        packages = next((p for p in site.getsitepackages() if Path(p).is_dir() and os.listdir(p)), "")
        hidden, wd, home = hidden.resolve(), wd.resolve(), home.resolve()
        script = """
import os, pathlib, socket, subprocess, sys
secret, sibling, binary, wd, home, port, packages = sys.argv[1:]
assert os.getcwd() == wd, os.getcwd()
for path, what in ((secret, "bench data"), (sibling, "Chanto sources")):
    try:
        pathlib.Path(path).read_text()
    except OSError:
        pass
    else:
        raise AssertionError(what + " readable")
if packages:
    assert os.listdir(packages) == [], "installed packages visible"
for path in (wd, home):
    p = pathlib.Path(path) / "allowed"
    p.write_text("ok")
    assert p.read_text() == "ok"
assert subprocess.check_output(["/bin/sh", binary, "ok"]).strip() == b"ok"
with socket.create_connection(("127.0.0.1", int(port)), timeout=5):
    pass
try:
    socket.create_connection(("1.1.1.1", 443), timeout=3)
except OSError:
    pass
else:
    raise AssertionError("external connection not denied")
"""
        sock_dir = Path(tempfile.mkdtemp(prefix="bench-net-test-"))
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            bridge = subprocess.Popen(["socat", f"UNIX-LISTEN:{sock_dir}/{port}.sock,fork,unlink-early", f"TCP:127.0.0.1:{port}"],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                time.sleep(0.3)
                with patch.object(run, "ROOT", hidden), patch.object(run, "CHANTO_REPO", hidden / "chanto"), \
                        patch.object(run, "WORK", hidden / "work"), patch.object(run, "AGENT_INSTALLS", []):
                    cmd = run.offline_linux(wd, home, [sys.executable, "-c", script, str(secret), str(sibling), str(binary), str(wd), str(home), str(port), packages],
                                            [port], sock_dir, binary)
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=wd)
            finally:
                bridge.kill()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(secret.read_text(), "original")

if __name__ == "__main__":
    unittest.main()
