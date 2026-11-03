"""Tests for overhead_report.py. The main one regenerates the October 31
overhead section from its own results files and compares it with the copy
of RESULTS.md in fixtures/."""
import json, re, shutil, tempfile, unittest
from pathlib import Path

import overhead_report as report

ROOT = Path(__file__).resolve().parent
# RESULTS.md, README.md and overhead-latest.json as the October 31 run left
# them. The live files change with every measurement, so the tests compare
# against this copy.
PUBLISHED = ROOT / "fixtures" / "overhead-2026-10-31"
MAC, LINUX = "results/overhead-20261031-064921.txt", "results/overhead-20261031-065121.txt"
WIN, WIN_OPENHANDS, WIN_MINI = ("results/overhead-20261031-180439.txt", "results/overhead-20261031-181631.txt",
                                "results/overhead-20261031-182303.txt")
RUN = 41176862324

# The data behind the October 31 table: the run, its jobs, and the Windows
# reruns (the run and job IDs are the ones RESULTS.md links to).
OCTOBER_31 = {"run_id": RUN, "pr": 14, "platforms": [
    {"os": "macOS", "runner": "macos-latest", "files": [{"path": MAC, "run_id": RUN, "job_id": 124466111397}]},
    {"os": "Linux", "runner": "ubuntu-latest", "files": [{"path": LINUX, "run_id": RUN, "job_id": 124466111535}]},
    {"os": "Windows", "runner": "windows-latest", "files": [
        {"path": WIN, "run_id": 41224112845, "job_id": 124604558328},
        {"path": WIN_OPENHANDS, "run_id": 41227780887},
        {"path": WIN_MINI, "run_id": 41228735404}]},
]}

# The one paragraph of the October 31 section that the generator doesn't
# write: a hand-written remark about that run's hardware. The generator reports
# a CPU change instead (summary["hardware_changed"]), for the pull request to
# raise with a reviewer.
HAND_WRITTEN = ("GitHub gave this run's Linux job an Intel Xeon where earlier runs had AMD EPYC\n"
                "chips, so compare agents within one run, not across runs.\n\n")


def published(name, heading):
    return report.split_section((PUBLISHED / name).read_text(encoding="utf-8"), heading)


def single_run(**windows):
    """October 31's files as if one run had measured all three OSes."""
    m = json.loads(json.dumps(OCTOBER_31))
    m.pop("pr")
    m["platforms"][2]["files"] = [{"path": WIN, "run_id": RUN, "job_id": 3, **windows}]
    return m


class OctoberThirtyFirst(unittest.TestCase):
    def test_reproduces_the_published_section(self):
        _, old, _ = published("RESULTS.md", "Overhead: ")
        self.assertIn(HAND_WRITTEN, old)
        section, _, _, summary = report.build(OCTOBER_31, old)
        self.assertEqual(section, old.replace(HAND_WRITTEN, ""))
        self.assertEqual(summary, {"missing": [], "did_not_run": {}, "hardware_changed": {},
                                   "chanto_version": "0.1.10"})

    def test_reproduces_the_readme_copy(self):
        _, old, _ = published("RESULTS.md", "Overhead: ")
        _, readme_old, _ = published("README.md", "Overhead: latest results")
        _, readme, _, _ = report.build(OCTOBER_31, old)
        self.assertEqual(readme, readme_old.replace(HAND_WRITTEN, ""))

    def test_latest_json(self):
        _, old, _ = published("RESULTS.md", "Overhead: ")
        _, _, data, _ = report.build(OCTOBER_31, old)
        self.assertEqual(data["chanto_version"], "0.1.10")
        self.assertEqual(data["date"], "2026-10-31")
        self.assertEqual(data["run_url"], f"https://github.com/chanto-sh/benchmarks/actions/runs/{RUN}")
        got = {os: (p["startup_ms"], p["cpu_ms_per_turn"], p["peak_mb"]) for os, p in data["platforms"].items()}
        self.assertEqual(got, {"macOS": (13, 1.5, 17), "Linux": (23, 3.1, 24), "Windows": (78, 3.1, 19)})
        # Every field the October 31 file had is still there, first, with the
        # same value, so readers of that file keep working.
        committed = json.loads((PUBLISHED / "overhead-latest.json").read_text())
        self.assertEqual(list(data)[:len(committed)], list(committed))
        for k in ("chanto_version", "date", "run_url"):
            self.assertEqual(data[k], committed[k])
        self.assertEqual(list(data["platforms"]), list(committed["platforms"]))
        for os_, old in committed["platforms"].items():
            new = data["platforms"][os_]
            self.assertEqual(list(new)[:len(old)], list(old), os_)
            self.assertEqual({k: new[k] for k in old}, old, os_)

    def test_latest_json_has_the_whole_table(self):
        _, old, _ = published("RESULTS.md", "Overhead: ")
        _, _, data, _ = report.build(OCTOBER_31, old)
        self.assertEqual(data["format"], 2)
        self.assertEqual(data["settings"], {"turns": 40, "file_kb": 40, "reps": 10})
        self.assertEqual((data["command"], data["sorted_by"]), ("python3 reproduce.py", "Linux"))
        # The table's rows, as the JSON has them: name, runtime, then each
        # metric for macOS, Linux and Windows, formatted as the table does.
        table = [[c.strip().strip("*") for c in line.strip("|").split("|")]
                 for line in old.splitlines() if line.startswith("| ") and not line.startswith("| agent")]
        self.assertEqual(len(table), 23)
        fmt = lambda v, f: report.DASH if v is None else format(v, f)
        oses = ["macOS", "Linux", "Windows"]
        rows = []
        for i, a in enumerate(data["agents"]):
            per_os = [data["platforms"][o]["agents"][i] for o in oses]
            self.assertEqual({r["id"] for r in per_os}, {a["id"]})
            rows.append([a["name"], a["runtime"]]
                        + [fmt(r[k], f) for k, f in (("startup_ms", ".0f"), ("cpu_ms_per_turn", ".1f"),
                                                     ("peak_mb", ".0f")) for r in per_os]
                        + [" / ".join(fmt(r["install_mb"], ",.0f") for r in per_os)])
        self.assertEqual(rows, table)
        self.assertEqual(data["agents"][0], {"id": "chanto", "name": "Chanto", "runtime": "Rust", "version": "0.1.10"})
        self.assertEqual({a["id"]: a["version"] for a in data["agents"]}["pi"], "1.1.0")
        # Each row names the file and job its numbers came from: on Windows,
        # OpenHands came from a rerun that has no job ID.
        win = data["platforms"]["Windows"]
        self.assertEqual(win["run_url"], "https://github.com/chanto-sh/benchmarks/actions/runs/41224112845")
        oh = next(r for r in win["agents"] if r["id"] == "openhands")
        self.assertEqual((oh["results"], oh["job_url"]),
                         (WIN_OPENHANDS, "https://github.com/chanto-sh/benchmarks/actions/runs/41227780887"))
        self.assertEqual(win["install_mb"], win["agents"][0]["install_mb"])
        self.assertEqual(data["platforms"]["Linux"]["machine"],
                         {"cpu": "Intel Xeon Platinum 8573C", "cores": 4, "memory_gb": 16, "os": "Linux 7.0 (Azure)",
                          "arch": "x86_64",
                          "description": "Intel Xeon Platinum 8573C, 4 cores, 16 GB RAM, Linux 7.0 (Azure), x86_64"})
        self.assertEqual(data["platforms"]["macOS"]["run_url"], data["run_url"])


class Render(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        (self.root / "results").mkdir()
        for f in ["RESULTS.md", "README.md"]:
            shutil.copyfile(PUBLISHED / f, self.root / f)
        for f in [MAC, LINUX, WIN, WIN_OPENHANDS, WIN_MINI]:
            shutil.copyfile(ROOT / f, self.root / f)

    def test_touches_only_the_overhead_sections(self):
        before, old, after = published("RESULTS.md", "Overhead: ")
        r_before, _, r_after = published("README.md", "Overhead: latest results")
        report.render(single_run(), self.root)
        b, new, a = report.split_section((self.root / "RESULTS.md").read_text(encoding="utf-8"), "Overhead: ")
        self.assertEqual((b, a), (before, after))
        self.assertNotEqual(new, old)
        rb, _, ra = report.split_section((self.root / "README.md").read_text(encoding="utf-8"), "Overhead: latest results")
        self.assertEqual((rb, ra), (r_before, r_after))
        self.assertTrue((self.root / "overhead-latest.json").exists())

    def test_one_run_for_every_os(self):
        report.render(single_run(), self.root)
        _, new, _ = report.split_section((self.root / "RESULTS.md").read_text(encoding="utf-8"), "Overhead: ")
        self.assertNotIn("measured separately", new)
        self.assertIn("on GitHub's own runners: `python3 reproduce.py`, the 23\n", new)
        self.assertIn("- **Windows**: `windows-latest`, AMD EPYC 7763, 4 cores, 16 GB RAM, Windows Server 2025, AMD64\n", new)
        self.assertIn(f"[Windows](https://github.com/chanto-sh/benchmarks/actions/runs/{RUN}#summary-3)", new)
        self.assertIn(f"(Linux), and [`{WIN}`]({WIN})\n(Windows).\n", new)
        # That run didn't get OpenHands or mini-swe-agent on Windows.
        self.assertIn("| OpenHands | Python | 5488 | 7271 | — | 85.0 | 98.3 | — | 341 | 320 | — | 626 / 620 / — |", new)
        # The JSON has that row too, with no numbers or file for Windows.
        data = json.loads((self.root / "overhead-latest.json").read_text())
        oh = next(r for r in data["platforms"]["Windows"]["agents"] if r["id"] == "openhands")
        self.assertEqual(oh, {"id": "openhands", "name": "OpenHands", "runtime": "Python", "startup_ms": None,
                              "cpu_ms_per_turn": None, "peak_mb": None, "install_mb": None})
        # The notes are carried over, and the README links to the new heading.
        self.assertIn("What isn't quite like for like:\n\n- Aider has no tool loop", new)
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        heading = re.search(r"^## (Overhead: .*)$", new, re.M)[1]
        self.assertIn(f"(RESULTS.md#{report.anchor(heading)})", readme)

    def test_reports_what_did_not_run(self):
        summary = report.render(single_run(), self.root)
        self.assertEqual(summary["did_not_run"], {"Windows": ["OpenHands", "mini-swe-agent"]})
        self.assertEqual(summary["hardware_changed"], {"Windows": {"was": "AMD EPYC", "now": "AMD EPYC 7763"}})

    def test_missing_platform(self):
        m = single_run()
        m["platforms"][2]["files"] = []
        summary = report.render(m, self.root)
        self.assertEqual(summary["missing"], ["Windows"])
        new = (self.root / "RESULTS.md").read_text(encoding="utf-8")
        self.assertIn("- **Windows**: `windows-latest`, not measured in this run\n", new)
        self.assertIn("| **Chanto** | Rust | **13** | **23** | — | **1.5** | **3.1** | — | **17** | **24** | — | 20 / 24 / — |", new)
        self.assertIn(" | Windows | CPU ms/turn, ", new)
        self.assertIsNone(json.loads((self.root / "overhead-latest.json").read_text())["platforms"]["Windows"])

    def test_sorts_by_another_os_without_linux(self):
        m = single_run()
        m["platforms"][1]["files"] = []
        report.render(m, self.root)
        new = (self.root / "RESULTS.md").read_text(encoding="utf-8")
        self.assertIn("Sorted by macOS CPU per turn.", new)

    def test_mixed_versions_are_refused(self):
        text = (self.root / LINUX).read_text(encoding="utf-8").replace("# goose: 1.54.0", "# goose: 1.55.0")
        (self.root / LINUX).write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(report.ReportError, "goose has different versions"):
            report.render(single_run(), self.root)

    def test_mixed_settings_are_refused(self):
        text = (self.root / LINUX).read_text(encoding="utf-8").replace("10 reps", "3 reps")
        (self.root / LINUX).write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(report.ReportError, "different settings"):
            report.render(single_run(), self.root)


class Parse(unittest.TestCase):
    def test_rows(self):
        res = report.parse_results((ROOT / WIN).read_text(encoding="utf-8"))
        self.assertEqual(res["rows"]["reasonix"], {"startup": 805, "cpu": 21.3, "rss": 72, "install": 59.2})
        self.assertIsNone(res["rows"]["mini"])  # "mini-swe-agentdid not run"
        self.assertIsNone(res["rows"]["openhands"])
        self.assertIsNone(res["versions"]["pi"])  # "unavailable: [WinError 193] ..."
        self.assertEqual(res["versions"]["chanto"], "0.1.10")
        self.assertEqual(res["settings"], (40, 40, 10))

    def test_runner_descriptions(self):
        cases = {
            "Apple M1 (Virtual) (VirtualMac2,1), 3 cores, 7 GB RAM, Darwin 25.6.0 arm64": ("Apple M1 (Virtual)", "macOS (Darwin 25.6.0)"),
            "INTEL(R) XEON(R) PLATINUM 8573C, 4 cores, 16 GB RAM, Linux 7.0.0-1017-azure x86_64": ("Intel Xeon Platinum 8573C", "Linux 7.0 (Azure)"),
            "AMD EPYC 7763 64-Core Processor, 4 cores, 16 GB RAM, Linux 6.11.0-1018-azure x86_64": ("AMD EPYC 7763", "Linux 6.11 (Azure)"),
            "AMD EPYC 9V74 80-Core Processor, 4 cores, 16 GB RAM, Windows 2025Server AMD64": ("AMD EPYC 9V74", "Windows Server 2025"),
        }
        for machine, (cpu, os_) in cases.items():
            got, m = report.cpu_name(machine)
            self.assertEqual((got, report.os_name(m)), (cpu, os_), machine)

    def test_anchor(self):
        self.assertEqual(report.anchor("Overhead: 23 agents, startup and per turn, mock model (October 31)"),
                         "overhead-23-agents-startup-and-per-turn-mock-model-october-31")


class Collect(unittest.TestCase):
    def test_from_artifacts(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        art, results = tmp / "artifacts", tmp / "results"
        results.mkdir()
        for d, f in [("overhead-macos-latest", MAC), ("overhead-ubuntu-latest", LINUX), ("overhead-retry-windows-latest", WIN)]:
            (art / d).mkdir(parents=True)
            shutil.copyfile(ROOT / f, art / d / Path(f).name)
        (art / "overhead-windows-latest").mkdir()  # the first attempt left nothing
        jobs = [{"id": 11, "name": "measure / overhead (macos-latest)"},
                {"id": 12, "name": "measure / overhead (ubuntu-latest)"},
                {"id": 13, "name": "measure / overhead (windows-latest)"},
                {"id": 23, "name": "retry / overhead (windows-latest)"}]
        m = report.collect(art, jobs, 99, results)
        got = [(p["os"], [(f["path"], f["job_id"]) for f in p["files"]]) for p in m["platforms"]]
        self.assertEqual(got, [("macOS", [(MAC, 11)]), ("Linux", [(LINUX, 12)]), ("Windows", [(WIN, 23)])])
        self.assertEqual(sorted(p.name for p in results.iterdir()), sorted(Path(f).name for f in [MAC, LINUX, WIN]))
        # An existing file with other contents is never overwritten.
        (results / Path(MAC).name).write_text("edited")
        with self.assertRaisesRegex(report.ReportError, "already exists"):
            report.collect(art, jobs, 99, results)

    def test_missing_os(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        (tmp / "results").mkdir()
        m = report.collect(tmp / "none", [], 99, tmp / "results")
        self.assertEqual([p["files"] for p in m["platforms"]], [[], [], []])


class Workflow(unittest.TestCase):
    def test_retries_only_what_did_not_fail(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        (tmp / "overhead-macos-latest").mkdir()
        shutil.copyfile(ROOT / MAC, tmp / "overhead-macos-latest" / Path(MAC).name)
        jobs = [{"name": "measure / overhead (macos-latest)", "conclusion": "success"},
                {"name": "measure / overhead (ubuntu-latest)", "conclusion": "failure"},
                {"name": "measure / overhead (windows-latest)", "conclusion": "cancelled"}]
        self.assertEqual(report.to_retry(tmp, jobs), ["windows-latest"])
        # A job that never showed up is retried too.
        self.assertEqual(report.to_retry(tmp, jobs[:2]), ["windows-latest"])

    def test_body(self):
        url = "https://github.com/chanto-sh/benchmarks/actions/runs/1"
        body = report.pr_body({"missing": [], "did_not_run": {}, "hardware_changed": {}}, "0.1.16", url)
        self.assertIn("Chanto 0.1.16", body)
        self.assertIn(f"[this auto-overhead run]({url})", body)
        self.assertNotIn("Draft", body)
        # Opened with the app's token, the checks start on their own.
        self.assertNotIn("reopen", body)
        body = report.pr_body({"missing": [], "did_not_run": {}, "hardware_changed": {}}, "0.1.16", url,
                              workflow_token=True)
        self.assertIn("close and reopen this pull request to start the checks", body)
        body = report.pr_body({"missing": ["Windows"], "did_not_run": {"Linux": ["Aider"]},
                               "hardware_changed": {"Linux": {"was": "AMD EPYC 7763", "now": "Intel Xeon"}}}, "0.1.16", url)
        self.assertIn("**Draft: no results for Windows.**", body)
        self.assertIn("On Linux, these agents made no measurable run and show dashes: Aider.", body)
        self.assertIn("(Intel Xeon) than the last table's (AMD EPYC 7763)", body)


if __name__ == "__main__":
    unittest.main()
