"""Runner regressions; BENCH_SANDBOX_SMOKE=1 adds the real sandbox check (sandbox-exec on macOS, bubblewrap on Linux)."""
import contextlib
import io
import hashlib
import http.server
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
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
        for name, value in {"WORK": self.root / "work", "RUNS": self.root / "work" / "runs", "TASKS": self.root / "tasks",
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

    def test_profile_reads_only_the_run_root_installs_and_system(self):
        root = run.WORK / 'runs/space "quote" \\ slash'
        install = self.root / "agents"
        binary = run.CHANTO_REPO / "target/release/chanto"
        profile = run.offline_profile(root, [install], binary)
        q = lambda p: json.dumps(str(Path(p).resolve()))
        # Nothing is readable or writable unless allowed, and the network is
        # localhost only.
        for rule in ("(deny file-read-data)", "(deny file-write*)", "(deny network*)",
                     '(allow network-outbound (remote ip "localhost:*"))', "(deny appleevent-send)"):
            self.assertIn(rule, profile)
        self.assertNotIn('"*:*"', profile)
        self.assertIn(f"(allow file-read* file-read-data file-write* (subpath {q(root)}))", profile)
        self.assertIn(f"(allow file-read* file-read-data (subpath {q(install)}))", profile)
        self.assertIn(f"(allow file-read* file-read-data (literal {q(binary)}))", profile)
        self.assertIn('(allow file-read-data (subpath "/usr"))', profile)
        # Only the run root is writable (and devices).
        writes = [l for l in profile.splitlines() if l.startswith("(allow") and "file-write*" in l]
        self.assertEqual(writes, ['(allow file-write* (subpath "/dev"))',
                                  f"(allow file-read* file-read-data file-write* (subpath {q(root)}))"])
        # This repository, the Chanto sources, bench data and installed packages
        # stay hidden even where a system or toolchain path covers them.
        for hidden in (run.ROOT, run.CHANTO_REPO, Path.home() / ".local/share/chanto-bench"):
            self.assertIn(f"(deny file-read-data file-write* (subpath {q(hidden)}))", profile)
        self.assertIn('(deny file-read-data file-write* (regex #"/(site|dist)-packages(/|$)"))', profile)
        names = run.CHECKOUT_NAMES
        self.assertIn(f'(deny file-read-data file-write* (regex #"/({names})/(tasks|results)(/|$)"))', profile)
        # Order matters: later rules win.
        first_allow = profile.index("(allow file-read* file-read-data")
        self.assertLess(profile.index("site|dist"), first_allow)
        self.assertLess(profile.index('(allow file-read-data (subpath "/usr"))'), profile.index("(deny file-read-data file-write*"))
        # Parents are listable by name (getcwd needs it), siblings are not.
        self.assertIn(f"(allow file-read-data (literal {q(Path(root).resolve().parent)}))", profile)
        self.assertNotIn(f"(subpath {q(Path(root).resolve().parent)})", profile)

    def test_public_benchmark_tasks_keep_system_packages_readable(self):
        root = run.WORK / "runs/r-1"
        keep = run.offline_profile(root, keep_site_packages=True)
        hide = run.offline_profile(root)
        deny = '(deny file-read-data file-write* (regex #"/(site|dist)-packages(/|$)"))'
        self.assertNotIn(deny, keep)
        self.assertIn(deny, hide)

    def test_each_agent_reads_only_its_own_install(self):
        with tempfile.TemporaryDirectory() as d:
            npm, bins, uv = Path(d) / "npm/node_modules/.bin", Path(d) / "bin", Path(d) / "uv"
            npm.mkdir(parents=True); bins.mkdir(); (bins / "goose").touch()
            with patch.object(run, "NPM_BIN", npm), patch.object(run, "BIN_DIR", bins), patch.object(run, "UV_TOOLS", uv):
                self.assertEqual(run.agent_installs("aider"), [uv / "aider-chat"])
                self.assertEqual(run.agent_installs("openhands"), [uv / "openhands"])
                self.assertEqual(run.agent_installs("goose"), [bins])
                self.assertEqual(run.agent_installs("claude"), [Path(d) / "npm"])
                self.assertEqual(run.agent_installs("chanto"), [])

    def test_isolation_mode_from_the_environment(self):
        with patch.object(run.sys, "platform", "darwin"):
            self.assertEqual(run.isolation_mode({}), "sandbox-exec")
            self.assertEqual(run.isolation_mode({"CHANTO_BENCH_ISOLATION": "on"}), "sandbox-exec")
            self.assertEqual(run.isolation_mode({"CHANTO_BENCH_ISOLATION": "off"}), "off")
            with self.assertRaises(SystemExit):
                run.isolation_mode({"CHANTO_BENCH_ISOLATION": "maybe"})
        with patch.object(run.sys, "platform", "linux"):
            self.assertEqual(run.isolation_mode({}), "bwrap")

    def test_each_run_gets_a_fresh_root_home_and_tmpdir(self):
        self.task()
        seen = []
        show = ("import os, json; print(json.dumps({k: os.environ[k] for k in "
                "('HOME', 'TMPDIR', 'XDG_CONFIG_HOME', 'PIP_NO_INDEX')})); print(os.getcwd())")
        with patch.object(run, "agent_cmd", return_value=([sys.executable, "-c", show], {})):
            for rep in (0, 1):
                r = run.run_task("fake", "tiny", "model", 100, 30, rep)
                env_line, cwd = (run.WORK / "fake" / f"tiny-{rep}.out").read_text().splitlines()
                seen.append((json.loads(env_line), cwd))
                self.assertEqual(r["isolation"], "off")
                self.assertEqual(r["offtask_hits"], [])
                self.assertTrue((run.WORK / "fake" / f"tiny-{rep}.patch").exists())
        (env0, cwd0), (env1, cwd1) = seen
        root0 = Path(cwd0).parent
        self.assertEqual(Path(env0["HOME"]), root0 / "home")
        self.assertEqual(Path(env0["TMPDIR"]), root0 / "tmp")
        self.assertTrue(env0["XDG_CONFIG_HOME"].startswith(env0["HOME"]))
        self.assertEqual(env0["PIP_NO_INDEX"], "1")
        self.assertNotEqual(root0, Path(cwd1).parent)
        # The roots are gone afterwards; the transcript and patch stay.
        self.assertFalse(root0.exists())
        self.assertEqual(list((run.WORK / "runs").iterdir()), [])

    def test_checkout_is_sealed_at_the_base_commit(self):
        wd = self.root / "ws"
        wd.mkdir()
        git = lambda *a: subprocess.run(["git", "-c", "user.email=b@b", "-c", "user.name=b", *a], cwd=wd, check=True,
                                        capture_output=True, text=True).stdout
        (wd / "a.py").write_text("base\n")
        git("init", "-q"); git("add", "-A"); git("commit", "-qm", "base")
        (wd / "a.py").write_text("FUTURE_FIX\n")
        git("commit", "-qam", "fix")
        future = git("rev-parse", "HEAD").strip()
        git("tag", "upstream-fix"); git("update-ref", "refs/remotes/origin/main", "HEAD")
        git("remote", "add", "origin", "https://github.com/example/upstream.git")
        git("reset", "-q", "--hard", "HEAD~1")
        info = run.seal_checkout(wd)
        self.assertEqual(info["commits"], 1)
        self.assertEqual(git("remote"), "")
        self.assertNotEqual(subprocess.run(["git", "cat-file", "-e", future], cwd=wd, capture_output=True).returncode, 0)
        everything = subprocess.run(["git", "cat-file", "--batch-all-objects", "--batch"], cwd=wd, capture_output=True).stdout
        self.assertNotIn(b"FUTURE_FIX", everything)
        git("fsck", "--lost-found")
        self.assertEqual(list((wd / ".git").glob("lost-found/*/*")), [])

    def test_offtask_hits_flag_what_isolation_is_for(self):
        root = (self.root / "work/runs/r-abcdefgh").resolve()
        (run.TASKS / "swe-x").mkdir(parents=True)
        (run.TASKS / "swe-x/instance.json").write_text(json.dumps({"repo": "pytest-dev/pytest"}))
        transcript = "\n".join([
            f"$ ls {root}/swe-x-0",  # its own root: fine
            f"$ cat {root.parent}/r-zyxwvuts/swe-x-0/src/_pytest/main.py",  # a sibling run
            "$ ls ~/.local/share/chanto-bench/work-hard-2/claude/swe-x-0",
            "$ pip download pytest==8.0 -d /tmp/x",
            "$ git fsck --lost-found",
            "$ find / -name 'python.py' 2>/dev/null",
            "WebFetch https://github.com/pytest-dev/pytest/pull/5103.diff",
            "$ curl https://api.github.com/repos/foo/bar/commits",
            "$ cat /Users/someone/IdeaProjects/other/notes.txt",
            "$ cat /usr/local/lib/python3.9/site-packages/_pytest/main.py",  # a newer pytest
            f"$ cat {root}/swe-x-0/.venv/lib/python3.9/site-packages/_pytest/main.py",  # the task's own venv
            "see https://github.com/pytest-dev/pytest/issues/5000",  # quoted by the prompt
        ])
        hits = run.offtask_hits([transcript], root, "swe-x", prompt="https://github.com/pytest-dev/pytest/issues/5000")
        kinds = {h["kind"] for h in hits}
        self.assertEqual(kinds, {"bench data", "package download", "git history", "whole-disk search", "web",
                                 "upstream repo", "path outside run root", "installed package"})
        self.assertEqual([h["text"] for h in hits if h["kind"] == "installed package"],
                         ["/usr/local/lib/python3.9/site-packages/_pytest/main.py"])
        texts = " ".join(h["text"] for h in hits)
        self.assertIn("r-zyxwvuts", texts)
        self.assertIn("/Users/someone/IdeaProjects/other/notes.txt", texts)
        self.assertNotIn("issues/5000", texts)
        self.assertNotIn("r-abcdefgh", texts)
        # A clean transcript, and the run's own long path wrapped over two lines, are clean.
        wrapped = f"cd {str(root)[:30]}\n    {str(root)[30:]}/swe-x-0 && pytest -q\n1 passed"
        self.assertEqual(run.offtask_hits([wrapped, "$ pytest testing/test_main.py"], root, "swe-x"), [])

    def test_report_refuses_unisolated_runs(self):
        results = [{"agent": "chanto", "task": "a", "rep": 0, "passed": True, "seconds": 1, "timed_out": False}]
        f = self.root / "r.json"
        for data in ({"isolation": "off"}, {"offline": True}, {}):
            with self.subTest(data=data):
                f.write_text(json.dumps({"model": "m", "ctx": 1, **data, "results": results}))
                with self.assertRaisesRegex(SystemExit, "without isolation"):
                    run.report([str(f)])
                self.assertIn("**Measured without isolation**", run.report([str(f)], unisolated=True))
        f.write_text(json.dumps({"model": "m", "ctx": 1, "isolation": "sandbox-exec", "results": results}))
        self.assertNotIn("without isolation", run.report([str(f)]))

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

    def test_sandbox_launch_timeout_or_error_leaves_no_run_root(self):
        self.task()
        popen = subprocess.Popen
        for launch_error in (False, True):

            def launch(cmd, *args, **kwargs):
                if cmd[0] == "sandbox-exec":
                    # Chanto's own sandbox is off inside the run's fresh home.
                    home = Path(kwargs["cwd"]).parent / "home"
                    self.assertEqual((home / "config.toml").read_text(), "[sandbox]\nenabled = false\n")
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
                    self.assertEqual(result["isolation"], "sandbox-exec")
            self.assertEqual(list((run.WORK / "runs").iterdir()), [])

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
        f.write_text(json.dumps({"model": "m", "ctx": 1, "isolation": "bwrap", "meta": {"upstream_model": "up/model"}, "results": results + results[:1]}))
        text = run.report([str(f), str(f)])
        self.assertIn("`up/model` (as `m`)", text)
        self.assertIn("| other | 3 | 1 | 1 | 1.00 (not significant) |", text)
        self.assertIn("**2/3**", text)  # a run listed twice counts once
        # Totals only count tasks every agent ran.
        extra = results + [{"agent": "chanto", "task": "d", "rep": 0, "passed": True, "seconds": 1, "timed_out": False}]
        f.write_text(json.dumps({"model": "m", "ctx": 1, "isolation": "bwrap", "results": extra}))
        text = run.report([str(f)])
        self.assertIn("Totals cover the 3 tasks every agent ran; 1 runs", text)
        self.assertIn("**2/3**", text)
        # Showcase tasks get their own totals and stay out of the coding score and pairing.
        show = results + [{"agent": a, "task": "data-x", "rep": 0, "passed": True, "seconds": 1, "timed_out": False}
                          for a in ("chanto", "other")]
        f.write_text(json.dumps({"model": "m", "ctx": 1, "isolation": "bwrap", "results": show}))
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
        f.write_text(json.dumps({"model": "m", "ctx": 1, "isolation": "bwrap", "results": results}))
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
                with self.subTest(offline=offline, budget=budget), \
                        patch.dict(os.environ, {"CHANTO_BENCH_ISOLATION": "on" if offline else "off"}):
                    for f in run.RESULTS.glob("*.json"):
                        f.unlink()
                    out = run.WORK / "chanto/tiny-0.out"
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text("budget exhausted" if budget else "done")
                    result = {"passed": not budget, "seconds": 0, "timed_out": False, "agent": "chanto"}
                    argv = ["run.py", "--tasks", "tiny"]
                    with patch.object(sys, "argv", argv), patch.object(run.sys, "platform", "darwin"), patch.object(run, "run_task", return_value=result), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        if budget:
                            with self.assertRaises(SystemExit):
                                run.main()
                        else:
                            run.main()
                    data = json.loads(next(run.RESULTS.glob("*.json")).read_text())
                    self.assertEqual(data["offline"], offline)
                    # Isolation is on unless turned off, and every file says which.
                    self.assertEqual(data["isolation"], "sandbox-exec" if offline else "off")
                    self.assertEqual(data["meta"]["isolation"], data["isolation"])
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

    def test_newer_agents_run_headless_against_the_proxy(self):
        wd = self.root / "wd"
        with patch.object(run, "API", "http://localhost:4000"):
            cmd, env = run.agent_cmd("codewhale", "m", "do it", 8192, wd)
            self.assertEqual(cmd[-3:], ["exec", "--auto", "do it"])
            self.assertIn('base_url = "http://localhost:4000/v1"', Path(cmd[cmd.index("--config") + 1]).read_text())
            self.assertEqual(env["CODEWHALE_TELEMETRY"], "0")

            cmd, env = run.agent_cmd("zerostack", "m", "do it", 8192, wd)
            self.assertIn("--dangerously-skip-permissions", cmd)
            cfg = (Path(env["ZS_CONFIG_DIR"]) / "config.toml").read_text()
            self.assertIn('base_url = "http://localhost:4000/v1"', cfg)
            self.assertIn("enable-exa-mcp = false", cfg)

            cmd, env = run.agent_cmd("hax", "m", "do it", 8192, wd)
            self.assertEqual(cmd[-1], "do it")
            self.assertEqual(env["HAX_OPENAI_BASE_URL"], "http://localhost:4000/v1")

            # Gemini CLI speaks the Gemini API, at the proxy's root.
            cmd, env = run.agent_cmd("gemini", "m", "do it", 8192, wd)
            self.assertEqual(cmd[-2:], ["-p", "do it"])
            self.assertIn("--yolo", cmd)
            self.assertEqual(env["GOOGLE_GEMINI_BASE_URL"], "http://localhost:4000")
        for a in ("codewhale", "zerostack", "hax", "gemini"):
            self.assertIn(a, run.VERSION_CMDS)

    def test_overhead_mock_speaks_gemini(self):
        import stressmock
        body = {"tools": [{"functionDeclarations": [
            {"name": "write_file", "parametersJsonSchema": {"type": "object", "properties": {"file_path": {"type": "string"}}}},
            {"name": "read_file", "parametersJsonSchema": {"type": "object", "properties": {"file_path": {"type": "string"}},
                                                           "required": ["file_path"]}}]}],
                "contents": [{"role": "user", "parts": [{"text": "Summarize the conversation so far"}]}]}
        self.assertEqual(stressmock.pick(body)[0], "read_file")
        self.assertTrue(stressmock.is_summary(body))
        # Structured output (Gemini CLI's side calls) gets schema-valid JSON.
        side = {"generationConfig": {"responseMimeType": "application/json", "responseJsonSchema": {
            "type": "object", "properties": {"next_speaker": {"type": "string", "enum": ["user", "model"]}}}}}
        self.assertEqual(json.loads(stressmock.structured_json(side)), {"next_speaker": "user"})

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

    def test_hosted_context_comes_from_the_proxy(self):
        """Every agent gets the hosted model's own window, not the local default."""
        info = {"data": [{"model_name": "other", "model_info": {"max_input_tokens": 8}},
                         {"model_name": "bench-model", "model_info": {"max_input_tokens": 1000000}}]}
        with patch.object(run, "API", "http://proxy"), \
                patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(info).encode())):
            self.assertEqual(run.hosted_context("bench-model"), 1000000)
        unknown = {"data": [{"model_name": "bench-model", "model_info": {}}]}
        with patch.object(run, "API", "http://proxy"), \
                patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(unknown).encode())), \
                self.assertRaises(SystemExit):
            run.hosted_context("bench-model")

    def test_run_roots_are_outside_home(self):
        """Config discovery walking up from a run must not reach the real HOME."""
        default = Path(tempfile.gettempdir()).resolve() / "chanto-bench-runs"
        self.assertNotIn(Path.home().resolve(), default.parents)
        root = run.new_run_root("fake", "tiny", 0)
        self.assertEqual(root.parent, run.RUNS.resolve())

    @unittest.skipUnless(os.environ.get("BENCH_SANDBOX_SMOKE") == "1" and (sys.platform == "darwin" or sys.platform.startswith("linux")),
                         "opt-in sandbox smoke: sandbox-exec on macOS, bubblewrap and socat on Linux")
    def test_isolated_run_sees_only_its_own_task(self):
        """One fake agent (a shell script) through run_task under the real
        sandbox: it reaches its checkout, its HOME and the proxy, and nothing
        else: not a sibling run, not the hidden tests, not GitHub, and not the
        upstream fix that the task's history had before it was sealed."""
        # A sibling run and another agent's transcript, as a concurrent shard would leave them.
        sibling = run.WORK / "runs/r-sibling0"
        sibling.mkdir(parents=True)
        (sibling / "secret.txt").write_text("the other run's patch")
        other_log = run.WORK / "other/tiny-0.out"
        other_log.parent.mkdir(parents=True)
        other_log.write_text("another agent's transcript")
        # A SWE-style task whose checkout first holds the upstream fix in its
        # history (a later commit, tag, remote ref and reflog), as a clone would.
        task = run.TASKS / "swe-tiny"
        (task / "files").mkdir(parents=True)
        (task / "files/a.py").write_text("x = 1\n")
        (task / "prompt.txt").write_text("Fix it")
        (task / "check.sh").write_text("exit 0\n")
        future_file = self.root / "future"
        (task / "setup.sh").write_text(
            "set -e\ngit init -q\ngit add -A\ngit -c user.email=b@b -c user.name=b commit -qm base\n"
            "echo FUTURE_FIX > a.py\ngit -c user.email=b@b -c user.name=b commit -qam upstream-fix\n"
            'git rev-parse HEAD > "$FUTURE_FILE"\ngit tag fix\ngit update-ref refs/remotes/origin/main HEAD\n'
            "git remote add origin https://github.com/example/upstream.git\ngit reset -q --hard HEAD~1\n")
        agent_dir = self.root / "agent"
        agent_dir.mkdir()
        script = agent_dir / "fake-agent.sh"
        script.write_text(r"""#!/bin/sh
probe() { name=$1; shift; echo "$ $*"; if "$@" >/dev/null 2>&1; then echo "REACHED $name"; else echo "BLOCKED $name"; fi; }
probe sibling-list ls "$SIBLING"
probe sibling-read cat "$SIBLING/secret.txt"
probe other-transcript cat "$OTHER_LOG"
probe hidden-tests cat "$TASK_DIR/check.sh"
probe write-outside sh -c "echo x > '$OUTSIDE/planted'"
probe github-ip python3 -c "import socket; socket.create_connection(('140.82.112.3', 443), timeout=5)"
probe github-name python3 -c "import socket; socket.create_connection(('github.com', 443), timeout=5)"
probe system-packages python3 -c "import os, site, sys; ps = [p for p in site.getsitepackages() if os.path.isdir(p)]; sys.exit(0 if any(os.listdir(p) for p in ps) else 1)"
probe proxy python3 -c "import sys, urllib.request as u; sys.exit(0 if u.build_opener(u.ProxyHandler({})).open(sys.argv[1], timeout=5).read() == b'proxy-ok' else 1)" "$FAKE_PROXY"
probe future-object git cat-file -e "$FUTURE"
probe future-content sh -c "git cat-file --batch-all-objects --batch | grep -a -q FUTURE_FIX"
probe future-log sh -c "git log --all --reflog --format=%s | grep -q upstream-fix"
probe lost-found sh -c "git fsck --lost-found; grep -r -a -q FUTURE_FIX .git/lost-found"
probe own-file grep -q "x = 1" a.py
probe own-write sh -c "echo y > own.txt && grep -q y own.txt"
probe home-write sh -c 'echo z > "$HOME/h" && grep -q z "$HOME/h"'
""")
        script.chmod(0o755)

        class Proxy(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"proxy-ok")

            def log_message(self, *a):
                pass

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Proxy)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        proxy = f"http://127.0.0.1:{server.server_address[1]}"

        def fake_agent(agent, model, prompt, ctx, wd=None):
            return ["/bin/sh", str(script)], {
                "SIBLING": str(sibling), "OTHER_LOG": str(other_log), "TASK_DIR": str(task), "OUTSIDE": str(other_log.parent),
                "FAKE_PROXY": proxy, "FUTURE": future_file.read_text().strip()}

        with patch.object(run, "OFFLINE", True), patch.object(run, "API", proxy), \
                patch.object(run, "agent_cmd", side_effect=fake_agent), \
                patch.object(run, "agent_installs", return_value=[agent_dir]), \
                patch.dict(os.environ, {"FUTURE_FILE": str(future_file)}):
            result = run.run_task("fake", "swe-tiny", "model", 100, 120, 0)
        out = (run.WORK / "fake/swe-tiny-0.out").read_text()
        verdicts = dict(reversed(line.split(" ", 1)) for line in out.splitlines() if line.startswith(("REACHED ", "BLOCKED ")))
        expected = {name: "REACHED" for name in ("proxy", "own-file", "own-write", "home-write")}
        expected.update({name: "BLOCKED" for name in (
            "sibling-list", "sibling-read", "other-transcript", "hidden-tests", "write-outside", "github-ip", "github-name",
            "system-packages", "future-object", "future-content", "future-log", "lost-found")})
        self.assertEqual(verdicts, expected, out)
        self.assertFalse((other_log.parent / "planted").exists())
        self.assertEqual(result["isolation"], "sandbox-exec" if sys.platform == "darwin" else "bwrap")
        # The attempts still show: the sibling run's path and the git history probe.
        kinds = {h["kind"] for h in result["offtask_hits"]}
        self.assertTrue({"bench data", "git history"} <= kinds, result["offtask_hits"])
        # Only the sibling is left: this run's root was cleaned up.
        self.assertEqual([p.name for p in (run.WORK / "runs").iterdir()], ["r-sibling0"])


if __name__ == "__main__":
    unittest.main()
