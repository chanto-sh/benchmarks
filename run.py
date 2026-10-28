#!/usr/bin/env python3
"""Benchmark coding agents on small, automatically-verified tasks.

Each task lives in tasks/<name>/ with:
  prompt.txt  - the instruction given to the agent
  files/      - the starting repository
  check.sh    - exit 0 if the task was solved (runs in the work dir;
                $OUTPUT_FILE points to the agent's captured output)
  setup.sh    - optional setup hook, run before the agent timer
  env         - optional KEY=VALUE lines exported to check.sh

Usage:
  run.py --agents chanto,opencode,claude --model qwen3.8-bench [--tasks a,b] [--repeat N]
  run.py --agents chanto,chanto+concise,chanto+effort,chanto+outline,chanto+quiet,chanto+all ...
      (experimental `[optimize]` switches via CHANTO_OPTIMIZE; --chanto-effort LEVEL for all chanto agents)
"""

import argparse
from contextlib import contextmanager, nullcontext
import signal
import fnmatch
import getpass
import hashlib
import json
import math
import random
import re
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS = ROOT / "tasks"
# Work dirs live outside this repo so agents can't wander into the Chanto sources.
# Not /tmp: a restart wipes it mid-run.
# Where the benchmark keeps installed agents, work folders and runs
# (install-agents.sh installs into the same place).
BENCH_HOME = Path(os.environ.get("BENCH_HOME", Path.home() / ".local/share/chanto-bench"))
WORK = Path(os.environ.get("BENCH_WORK", BENCH_HOME / "work"))
# Run roots go outside HOME: agents look for config in every folder above their
# working directory, and one that reaches a denied ~/.claude or ~/.config can
# fail to start (opencode does) instead of skipping it.
RUNS = Path(os.environ.get("BENCH_RUNS", Path(tempfile.gettempdir()).resolve() / "chanto-bench-runs"))
RESULTS = ROOT / "results"
# The Chanto checkout under test: its release binary by default, and like this
# repository it's hidden from the agents. A sibling clone unless set.
CHANTO_REPO = Path(os.environ.get("CHANTO_REPO", ROOT.parent / "chanto")).resolve()
# Directory names a checkout of this repository goes by: its usual clone names,
# the bench/ folder it grew out of, and whatever this one is called.
# POSIX extended syntax (the macOS sandbox's), so only its metacharacters are escaped.
CHECKOUT_NAMES = "|".join(sorted({"bench", "[^/]*benchmarks", re.sub(r"([.^$*+?()\[\]{}|\\])", r"\\\1", ROOT.name)}))
# Agents installed with npm into an isolated prefix (see README).
NPM_BIN = Path(os.environ.get("BENCH_NPM_BIN", BENCH_HOME / "agents/node_modules/.bin"))
# cline ships its launcher outside .bin, so name it directly.
CLINE_BIN = Path(os.environ.get("BENCH_CLINE_BIN", NPM_BIN.parent / "cline" / "bin" / "cline"))
# Agents shipped as standalone binaries (opencode, goose, codewhale, zerostack,
# hax), pinned and checksummed.
BIN_DIR = Path(os.environ.get("BENCH_BIN_DIR", BENCH_HOME / "bin"))
# Python agents installed with `uv tool install`, each in its own environment.
UV_TOOLS = Path.home() / ".local/share/uv/tools"
AGENT_INSTALLS = [NPM_BIN.parent.parent, BIN_DIR, UV_TOOLS / "aider-chat", UV_TOOLS / "openhands"]


def agent_exe(name):
    """The benchmark's own pinned install of an agent: the npm prefix, the
    binaries directory, or its uv tool environment. A copy on the user's PATH is
    only the fallback, so a global upgrade can't change what a run measures."""
    tool = {"aider": "aider-chat"}.get(name, name)
    for p in (NPM_BIN / name, BIN_DIR / name, UV_TOOLS / tool / "bin" / name):
        if p.exists():
            return str(p)
    return name
# BENCH_CHANTO_BIN pins a frozen build for long runs (so rebuilding doesn't change it mid-run).
CHANTO_BIN = Path(os.environ.get("BENCH_CHANTO_BIN", CHANTO_REPO / "target" / "release" / "chanto"))


def home(agent):
    """A fresh, empty config home: nobody gets the user's personal settings,
    plugins, MCP servers or memories. During a run it's that run's own HOME
    (one agent per run root); outside one, a per-agent folder in WORK."""
    d = RUN_HOME if RUN_HOME is not None else WORK / ".homes" / agent
    d.mkdir(parents=True, exist_ok=True)
    return d


def source_files(wd):
    """Non-test source files (Aider needs the files it may edit named up front)."""
    out = []
    for p in sorted(wd.rglob("*")):
        rel = p.relative_to(wd).as_posix()
        if p.is_file() and not rel.startswith((".git/", "target/", ".venv/")) and not TEST_RE.search(rel if "/" in rel else p.name) \
                and p.suffix in (".py", ".go", ".rs", ".js", ".ts", ".toml", ".mod", ".json", ".md", ".csv", ".txt") and p.stat().st_size < 200_000:
            out.append(rel)
    return out


# --api: every agent talks to one OpenAI/Anthropic-compatible proxy (proxy.sh)
# instead of the local Ollama server.
API = None
API_KEY = "sk-bench-local"
# --meter: route each run through meter.py under its own label, so every
# Chanto's token use is counted the same way.
METER = None
METER_LOG = None
# --chanto-effort: one reasoning effort for every chanto variant, so an
# `chanto+effort` run on a chat-completions model (where chanto knows no
# default effort) compares like with like.
CHANTO_EFFORT = None

# Experimental chanto optimizations (`[optimize]`, off by default), turned on
# per agent name: `chanto+concise`, `chanto+quiet`, `chanto+provenance`,
# `chanto+spec`, `chanto+all`.
# `quiet` is quiet mode's model side (no narration between tool calls, one
# short summary); its TUI view doesn't apply to these -p json runs.
OPTIMIZE_FLAGS = {"concise": "concise_prose", "quiet": "quiet", "provenance": "provenance", "spec": "spec_check",
                  "adaptive": "adaptive_effort", "noadaptive": "no_adaptive_effort",
                  "prefix": "stable_prefix", "noprefix": "no_stable_prefix",
                  "defer": "defer_tools", "token": "token_classifier"}


def chanto_optimizations(agent):
    """The optimization short names a `chanto+…` agent turns on (empty for others)."""
    if not agent.startswith("chanto+"):
        return []
    names = agent.split("+")[1:]
    if names == ["all"]:
        # `spec_check` is opt-in only: it traded ~20% more tokens for a gain
        # inside the noise band, so it isn't part of the default set.
        # `defer` and `token` are selected by name while they're measured;
        # `adaptive` and `prefix` are defaults, `noadaptive`/`noprefix` their opposites.
        return [n for n in OPTIMIZE_FLAGS if n not in ("spec", "adaptive", "noadaptive", "prefix", "noprefix", "defer", "token")]
    unknown = [n for n in names if n not in OPTIMIZE_FLAGS]
    if unknown or not names or len(set(names)) != len(names):
        raise SystemExit(f"agent {agent}: optimizations are {', '.join(OPTIMIZE_FLAGS)} or all, joined with +")
    return names


def chanto_extra(agent):
    """CLI args and env for a chanto variant: its optimizations and the shared effort."""
    args = ["--effort", CHANTO_EFFORT] if CHANTO_EFFORT else []
    flags = chanto_optimizations(agent)
    # Always set, so a CHANTO_OPTIMIZE in the runner's own environment can't reach the baseline.
    return args, {"CHANTO_OPTIMIZE": ",".join(flags) or "none"}


def hosted_cmd(agent, model, prompt, ctx, wd):
    """Commands for a hosted model behind the LiteLLM proxy at API."""
    v1 = f"{API}/v1"
    h = {"CHANTO_HOME": str(home("chanto")), "CHANTO_COMPAT_HOME": str(home("chanto") / "compat"), "CHANTO_API_KEY": API_KEY,
         # No presence: a benchmark run must not be steered by, or appear to, another
         # chanto session sharing the same work dir or home.
         "CHANTO_NO_PRESENCE": "1"}
    base = [str(CHANTO_BIN), "-p", "--provider", "openai", "--base-url", v1, "--model", model, "--num-ctx", str(ctx), "--output-format", "json"]
    if agent.startswith("chanto"):
        extra, env = chanto_extra(agent)
        h.update(env)
    if agent == "chanto" or agent.startswith("chanto+"):
        return base + extra + ["--mode", "bypassPermissions", prompt], h
    if agent == "chanto-verify":
        return base + extra + ["--mode", "bypassPermissions", "--verify", prompt], h
    if agent == "opencode":
        cfg = home("opencode") / "opencode.json"
        cfg.write_text(json.dumps({
            "$schema": "https://opencode.ai/config.json",
            "provider": {"bench": {"npm": "@ai-sdk/openai-compatible", "name": "Bench", "options": {"baseURL": v1, "apiKey": API_KEY},
                                   "models": {model: {"name": model, "tools": True}}}},
            "permission": {"edit": "allow", "bash": "allow", "webfetch": "allow"},
        }))
        return [agent_exe("opencode"), "run", "--standalone", "--auto", "-m", f"bench/{model}", prompt], {
            "OPENCODE_CONFIG": str(cfg), "XDG_CONFIG_HOME": str(home("opencode") / "xdg"), "XDG_DATA_HOME": str(home("opencode") / "data")}
    if agent == "claude":
        env = {"ANTHROPIC_BASE_URL": API, "ANTHROPIC_AUTH_TOKEN": API_KEY, "ANTHROPIC_API_KEY": "", "ANTHROPIC_MODEL": model,
               "ANTHROPIC_DEFAULT_HAIKU_MODEL": model, "ANTHROPIC_DEFAULT_SONNET_MODEL": model, "ANTHROPIC_DEFAULT_OPUS_MODEL": model,
               "CLAUDE_CODE_SUBAGENT_MODEL": model, "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "CLAUDE_CONFIG_DIR": str(home("claude"))}
        return [agent_exe("claude"), "-p", "--model", model, "--dangerously-skip-permissions", "--output-format", "json", prompt], env
    if agent == "codex":
        (home("codex") / "config.toml").write_text(
            f'model_provider = "bench"\n[model_providers.bench]\nname = "bench"\nbase_url = "{v1}"\nenv_key = "BENCH_API_KEY"\nwire_api = "responses"\n')
        return [agent_exe("codex"), "exec", "-m", model, "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check", prompt], {
            "CODEX_HOME": str(home("codex")), "BENCH_API_KEY": API_KEY}
    if agent == "aider":
        files = source_files(wd) if wd else []
        return [agent_exe("aider"), "--model", f"openai/{model}", "--yes-always", "--no-auto-commits", "--no-check-update", "--analytics-disable",
                "--no-show-model-warnings", "--no-pretty", "--no-stream", "--no-gitignore", "--message", prompt, *files], {
            "OPENAI_API_BASE": v1, "OPENAI_API_KEY": API_KEY, "AIDER_HOME": str(home("aider"))}
    if agent == "goose":
        return [agent_exe("goose"), "run", "--no-session", "--quiet", "-t", prompt], {
            "GOOSE_PROVIDER": "openai", "GOOSE_MODEL": model, "OPENAI_HOST": API, "OPENAI_API_KEY": API_KEY, "GOOSE_MODE": "auto",
            "GOOSE_DISABLE_KEYRING": "1", "XDG_CONFIG_HOME": str(home("goose") / "xdg"), "XDG_DATA_HOME": str(home("goose") / "data"),
            "XDG_STATE_HOME": str(home("goose") / "state")}
    nb = NPM_BIN
    if agent == "cline":
        # `cline auth` writes this file; writing it directly keeps the call
        # offline-safe (no extra process) and pins the run to the proxy.
        d = home("cline")
        (d / "settings").mkdir(parents=True, exist_ok=True)
        # A missing `updatedAt` fails cline's schema check and it silently
        # falls back to api.openai.com, so keep it alongside the settings.
        (d / "settings" / "providers.json").write_text(json.dumps({
            "version": 1, "lastUsedProvider": "openai-compatible", "modes": {},
            "providers": {"openai-compatible": {
                "settings": {"provider": "openai-compatible", "apiKey": API_KEY, "model": model, "baseUrl": v1},
                "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tokenSource": "manual"}}}))
        return [str(CLINE_BIN), "--yolo", "--json", "-P", "openai-compatible", "-m", model, "-k", API_KEY,
                "--config", str(d), "--data-dir", str(d), prompt], {"CLINE_DIR": str(d)}
    if agent == "pi":
        d = home("pi")
        (d / "models.json").write_text(json.dumps({"providers": {"bench": {
            "baseUrl": v1, "api": "openai-completions", "apiKey": API_KEY,
            "models": [{"id": model, "contextWindow": ctx}]}}}))
        return [str(nb / "pi"), "-p", "--no-session", "--provider", "bench", "--model", model, prompt], {"PI_CODING_AGENT_DIR": str(d)}
    if agent == "crush":
        xdg = home("crush") / "xdg"
        (xdg / "crush").mkdir(parents=True, exist_ok=True)
        (xdg / "crush" / "crush.json").write_text(json.dumps({
            "providers": {"bench": {"type": "openai", "base_url": v1, "api_key": API_KEY,
                                    "models": [{"id": model, "name": model, "context_window": ctx, "default_max_tokens": 8192}]}},
            "models": {"large": {"model": model, "provider": "bench"}, "small": {"model": model, "provider": "bench"}},
            "options": {"disable_metrics": True}}))
        tmp = home("crush") / "tmp"
        tmp.mkdir(exist_ok=True)
        return [str(nb / "crush"), "run", "--quiet", "-D", str(home("crush") / "data"), "-m", f"bench/{model}", prompt], {
            "XDG_CONFIG_HOME": str(xdg), "XDG_DATA_HOME": str(home("crush") / "data"), "TMPDIR": str(tmp), "CRUSH_DISABLE_METRICS": "1"}
    if agent == "qwen":
        h = home("qwen")
        (h / ".qwen").mkdir(exist_ok=True)
        (h / ".qwen" / "settings.json").write_text(json.dumps({"security": {"auth": {"selectedType": "openai"}}, "usageStatisticsEnabled": False}))
        return [str(nb / "qwen"), "--yolo", "-m", model, prompt], {
            "HOME": str(h), "OPENAI_API_KEY": API_KEY, "OPENAI_BASE_URL": v1, "OPENAI_MODEL": model}
    if agent == "forge":
        # forge 2.13+ no longer reads OPENAI_* env vars: it needs an explicit
        # provider in .forge.toml and the key in .credentials.json, or it exits
        # with "Device not configured (os error 6)". The credentials file also
        # pins the endpoint URL, and --meter rewrites API per run, so give forge
        # a fresh HOME per task instead of a shared one.
        h = home("forge") / (wd.name if wd else "default")
        shutil.rmtree(h, ignore_errors=True)
        (h / ".forge").mkdir(parents=True)
        (h / ".forge" / ".forge.toml").write_text(f'''[[providers]]
id = "bench"
url = "{v1}/chat/completions"
response_type = "OpenAI"
models = [{{ id = "{model}", name = "{model}", context_length = {ctx}, tools_supported = true }}]

[session]
provider_id = "bench"
model_id = "{model}"
''')
        (h / ".forge" / ".credentials.json").write_text(
            json.dumps([{"id": "bench", "auth_details": {"api_key": API_KEY}}]))
        return [str(nb / "forge"), "-p", prompt], {"HOME": str(h)}
    if agent == "kilo":
        cfg = home("kilo") / "kilo.json"
        cfg.write_text(json.dumps({
            "$schema": "https://app.kilo.ai/config.json",
            "provider": {"bench": {"npm": "@ai-sdk/openai-compatible", "name": "Bench", "options": {"baseURL": v1, "apiKey": API_KEY},
                                   "models": {model: {"name": model, "tools": True}}}},
            "permission": {"edit": "allow", "bash": "allow", "webfetch": "allow"},
        }))
        return [str(nb / "kilo"), "run", "--auto", "-m", f"bench/{model}", prompt], {
            "KILO_CONFIG": str(cfg), "OPENCODE_CONFIG": str(cfg), "XDG_CONFIG_HOME": str(home("kilo") / "xdg"), "XDG_DATA_HOME": str(home("kilo") / "data")}
    if agent == "cn":
        # Continue's CLI: a local config.yaml with one OpenAI-compatible model,
        # --auto to allow every tool, and its own HOME (it also reads
        # ~/.claude/settings.json) and global dir; telemetry off, as for the rest.
        h = home("cn")
        cfg = h / "config.yaml"
        cfg.write_text(json.dumps({
            "name": "bench", "version": "1.0.0", "schema": "v1",
            "models": [{"name": model, "provider": "openai", "model": model, "apiBase": v1, "apiKey": API_KEY,
                        "roles": ["chat", "edit", "apply"], "capabilities": ["tool_use"],
                        "defaultCompletionOptions": {"contextLength": ctx}}]}))
        return [str(nb / "cn"), "-p", "--auto", "--config", str(cfg), prompt], {
            "HOME": str(h), "CONTINUE_GLOBAL_DIR": str(h / ".continue"),
            "CONTINUE_CLI_ENABLE_TELEMETRY": "0", "CONTINUE_METRICS_ENABLED": "0"}
    if agent == "openhands":
        # The OpenHands CLI (uv tool): headless mode auto-approves actions, and
        # --override-with-envs takes the model from LLM_* (LiteLLM naming, so
        # openai/<model> against the proxy). Its own HOME keeps ~/.openhands apart.
        h = home("openhands")
        return [agent_exe("openhands"), "--headless", "--override-with-envs", "--exit-without-confirmation", "-t", prompt], {
            "HOME": str(h), "LLM_MODEL": f"openai/{model}", "LLM_BASE_URL": v1, "LLM_API_KEY": API_KEY,
            "OPENHANDS_SUPPRESS_BANNER": "1"}
    if agent == "codewhale":
        # A named OpenAI-compatible provider in its own CODEWHALE_HOME; `exec
        # --auto` is its headless mode with tool use auto-approved. Telemetry
        # (on by default) and the update check are switched off.
        h = home("codewhale")
        cfg = h / "config.toml"
        cfg.write_text(f'provider = "bench"\ndefault_text_model = "{model}"\n\n[providers.bench]\nkind = "openai-compatible"\n'
                       f'base_url = "{v1}"\napi_key = "{API_KEY}"\nmodel = "{model}"\n')
        return [agent_exe("codewhale"), "--config", str(cfg), "--provider", "bench", "--model", model, "exec", "--auto", prompt], {
            "HOME": str(h), "CODEWHALE_HOME": str(h / ".codewhale"), "CODEWHALE_CONFIG_PATH": str(cfg),
            "CODEWHALE_TELEMETRY": "0", "CODEWHALE_NO_UPDATE_CHECK": "1"}
    if agent == "zerostack":
        # A custom OpenAI-compatible provider in its own config and data dirs;
        # --dangerously-skip-permissions approves every tool call. Its default
        # Exa web-search MCP server (a remote service) is turned off.
        h = home("zerostack")
        cfg = h / "config"
        cfg.mkdir(exist_ok=True)
        (cfg / "config.toml").write_text(
            f'context_window = {ctx}\nenable-exa-mcp = false\n\n[custom_providers.bench]\nprovider_type = "openai"\nbase_url = "{v1}"\n'
            f'api_key_env = "BENCH_API_KEY"\nmodel = "{model}"\n')
        return [agent_exe("zerostack"), "-p", "--no-session", "--dangerously-skip-permissions", "--provider", "bench",
                "--model", model, prompt], {
            "HOME": str(h), "ZS_CONFIG_DIR": str(cfg), "ZS_DATA_DIR": str(h / "data"), "BENCH_API_KEY": API_KEY}
    if agent == "hax":
        # hax has no permission prompts; its openai-compatible provider is
        # configured from HAX_* variables, with XDG dirs kept in its own home.
        h = home("hax")
        return [agent_exe("hax"), "-p", "--no-session", "--provider=openai-compatible", f"--model={model}", prompt], {
            "HAX_OPENAI_BASE_URL": v1, "HAX_OPENAI_API_KEY": API_KEY, "HAX_CONTEXT_LIMIT": str(ctx),
            "XDG_CONFIG_HOME": str(h / "config"), "XDG_STATE_HOME": str(h / "state"), "XDG_CACHE_HOME": str(h / "cache"),
            "XDG_DATA_HOME": str(h / "data")}
    if agent == "gemini":
        # Gemini CLI speaks only the Gemini API; GOOGLE_GEMINI_BASE_URL points
        # it at the endpoint. --yolo approves every tool; its own HOME keeps
        # ~/.gemini apart, with telemetry and update checks off.
        h = home("gemini")
        (h / ".gemini").mkdir(exist_ok=True)
        (h / ".gemini" / "settings.json").write_text(json.dumps({
            "security": {"auth": {"selectedType": "gemini-api-key"}, "folderTrust": {"enabled": False}},
            "privacy": {"usageStatisticsEnabled": False}, "telemetry": {"enabled": False},
            "general": {"disableAutoUpdate": True, "disableUpdateNag": True}}))
        return [str(nb / "gemini"), "--yolo", "-m", model, "-p", prompt], {
            "HOME": str(h), "GEMINI_API_KEY": API_KEY, "GOOGLE_GEMINI_BASE_URL": API}
    raise SystemExit(f"agent {agent} has no hosted (--api) configuration")


def agent_cmd(agent, model, prompt, ctx, wd=None):
    if API:
        return hosted_cmd(agent, model, prompt, ctx, wd)
    chanto_env = {"CHANTO_HOME": str(home("chanto")), "CHANTO_COMPAT_HOME": str(home("chanto") / "compat"),
                   "CHANTO_NO_PRESENCE": "1"}
    extra = []
    if agent.startswith("chanto"):
        extra, env = chanto_extra(agent)
        chanto_env.update(env)
    if agent == "chanto" or agent.startswith("chanto+"):
        return [str(CHANTO_BIN), "-p", "--mode", "bypassPermissions", *extra, "--model", model,
                "--num-ctx", str(ctx), "--output-format", "json", prompt], chanto_env
    if agent == "chanto-verify":
        return [str(CHANTO_BIN), "-p", "--mode", "bypassPermissions", "--verify", *extra, "--model", model,
                "--num-ctx", str(ctx), "--output-format", "json", prompt], chanto_env
    if agent == "chanto-auto":
        return [str(CHANTO_BIN), "-p", "--mode", "auto", *extra, "--model", model,
                "--num-ctx", str(ctx), "--output-format", "json", prompt], chanto_env
    if agent == "opencode":
        cfg = home("opencode") / "opencode.json"
        cfg.write_text(json.dumps({
            "$schema": "https://opencode.ai/config.json",
            "provider": {"ollama": {"npm": "@ai-sdk/openai-compatible", "name": "Ollama",
                                    "options": {"baseURL": "http://localhost:11434/v1"},
                                    "models": {model: {"name": model, "tools": True, "reasoning": True}}}},
            "permission": {"edit": "allow", "bash": "allow", "webfetch": "allow"},
        }))
        return [agent_exe("opencode"), "run", "--standalone", "--auto", "-m", f"ollama/{model}", prompt], {
            "OPENCODE_CONFIG": str(cfg), "XDG_CONFIG_HOME": str(home("opencode") / "xdg"), "XDG_DATA_HOME": str(home("opencode") / "data")}
    if agent == "claude":
        env = {
            "ANTHROPIC_BASE_URL": "http://localhost:11434",
            "ANTHROPIC_AUTH_TOKEN": "ollama",
            "ANTHROPIC_API_KEY": "",
            "ANTHROPIC_MODEL": model,
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": model,
            "ANTHROPIC_DEFAULT_SONNET_MODEL": model,
            "ANTHROPIC_DEFAULT_OPUS_MODEL": model,
            "CLAUDE_CODE_SUBAGENT_MODEL": model,
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            "CLAUDE_CONFIG_DIR": str(home("claude")),
        }
        return [agent_exe("claude"), "-p", "--model", model, "--dangerously-skip-permissions", "--output-format", "json", prompt], env
    if agent == "codex":
        # Codex's local mode looks the model up by exact tag (and tries to pull it otherwise).
        return [agent_exe("codex"), "exec", "--oss", "--local-provider", "ollama", "-m", model if ":" in model else f"{model}:latest",
                "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check", prompt], {"CODEX_HOME": str(home("codex"))}
    if agent == "aider":
        settings = home("aider") / "model-settings.yml"
        settings.write_text(f"- name: ollama_chat/{model}\n  extra_params:\n    num_ctx: {ctx}\n")
        files = source_files(wd) if wd else []
        return [agent_exe("aider"), "--model", f"ollama_chat/{model}", "--model-settings-file", str(settings), "--yes-always",
                "--no-auto-commits", "--no-check-update", "--analytics-disable", "--no-show-model-warnings",
                "--no-pretty", "--no-stream", "--no-gitignore", "--message", prompt, *files], {
            "OLLAMA_API_BASE": "http://127.0.0.1:11434", "AIDER_HOME": str(home("aider"))}
    if agent == "goose":
        return [agent_exe("goose"), "run", "--no-session", "--quiet", "-t", prompt], {
            "GOOSE_PROVIDER": "ollama", "GOOSE_MODEL": model, "OLLAMA_HOST": "http://localhost:11434",
            "GOOSE_MODE": "auto", "GOOSE_DISABLE_KEYRING": "1", "XDG_CONFIG_HOME": str(home("goose") / "xdg"),
            "XDG_DATA_HOME": str(home("goose") / "data"), "XDG_STATE_HOME": str(home("goose") / "state")}
    raise SystemExit(f"unknown agent {agent}")


TEST_RE = re.compile(r"(^test_.*\.py$|_test\.(py|go)$|\.(test|spec)\.[jt]sx?$|^tests?/)")


def test_files(wd):
    """Hashes of test files (to detect an agent editing or deleting tests)."""
    out = {}
    for p in wd.rglob("*"):
        rel = p.relative_to(wd).as_posix()
        if p.is_file() and not rel.startswith((".git/", ".venv/")) and "node_modules" not in rel and TEST_RE.search(rel if "/" in rel else p.name):
            out[rel] = hashlib.sha1(p.read_bytes()).hexdigest()
    return out


OUT_OF_BUDGET = re.compile(r"402 Payment Required|Insufficient Balance|budget exhausted|BudgetExceeded|Budget has been exceeded|exceeded your current quota|insufficient_quota", re.I)


def metered(label):
    """Provider-reported usage for one run, from the meter log (None without --meter)."""
    if not label:
        return None
    time.sleep(0.5)  # let the meter finish writing the last response
    from meter import totals
    return totals(METER_LOG).get(label, {"requests": 0, "input": 0, "output": 0, "cached": 0})


# --------------------------------------------------------------------- tiers
# Tasks in three difficulty bands. The core band is small, self-contained katas
# (Aider's polyglot exercises, EvalPlus HumanEval+/MBPP+) that a strong model
# solves nearly every time (a ceiling check, not a differentiator); hard is real
# GitHub issues (SWE-bench Lite and Verified) where models actually diverge. A
# good suite mixes the two so it can show both "does it work at all" and "how
# much better is it". "beyond" is coding with an honesty twist:
# hidden-parameter tests that catch hardcoding and faked "done", simulations and
# solvers, and impossible tasks (trap-imp-*) where the pass is saying so.
# "showcase" (data analysis, root-causing, docs/config work, FinQA's financial
# tables) produces answers rather than code: it is opt-in and never part of the
# headline coding score. DS-1000's data-science problems stay in medium because
# they are graded as code.
TIERS = ["core", "medium", "hard", "beyond", "showcase"]
CODING_TIERS = ["core", "medium", "hard", "beyond"]
BEYOND = ("coding-", "math-", "physics-", "trap-imp-")
SHOWCASE = ("data-", "analysis-", "nontrad-", "finqa-")
# Price per token (USD), matching proxy.sh, so an estimate needs no live call.
# Each model maps to (off_peak, peak), both a (input, cache_hit, output) triple.
# Agents resend their history every call, so most input tokens arrive as cache
# hits — pricing them at the plain input rate overstates a run several-fold.
# DeepSeek's off-peak rate is half of peak; peak is 01:00-04:00 and 06:00-10:00
# UTC Mon-Fri, all other hours (and weekends) are off-peak.
# `deepseek-flash` serves DeepSeek-V4.1-Flash-1017 (V4-Flash is retired); the
# legacy `deepseek-v4-flash` name is accepted and billed identically.
PRICES = {
    "deepseek/deepseek-flash": ((0.15e-6, 0.003e-6, 0.60e-6), (0.30e-6, 0.006e-6, 1.20e-6)),
    "deepseek/deepseek-v4-flash": ((0.15e-6, 0.003e-6, 0.60e-6), (0.30e-6, 0.006e-6, 1.20e-6)),
    "deepseek/deepseek-v4-pro": ((0.66e-6, 0.022e-6, 1.98e-6), (1.32e-6, 0.044e-6, 3.96e-6)),
    # OpenRouter doesn't publish a cache rate for this one; charge cache hits as input.
    "openrouter/qwen/qwen3.5-9b": ((0.10e-6, 0.10e-6, 0.15e-6), (0.10e-6, 0.10e-6, 0.15e-6)),
}


def cost_of(tin, tout, tcache, price):
    """USD for a token tally: uncached input, cache hits, and output."""
    p_in, p_cache, p_out = price
    return (tin - tcache) * p_in + tcache * p_cache + tout * p_out


def tier_of(task):
    """Difficulty band from the task name; anything hand-written is 'medium'."""
    if task.startswith("swe-"):
        return "hard"
    if task.startswith(SHOWCASE):
        return "showcase"
    if task.startswith(BEYOND):
        return "beyond"
    if task.startswith(("poly-", "humaneval-", "mbpp-", "trap-")):
        return "core"
    return "medium"


def select_tasks(tiers, patterns):
    """Tasks in the requested tiers, narrowed by comma-separated name globs."""
    tasks = sorted(p.name for p in TASKS.iterdir() if p.is_dir())
    tasks = [t for t in tasks if tier_of(t) in tiers]
    if patterns:
        tasks = [t for t in tasks if any(fnmatch.fnmatchcase(t, p) for p in patterns.split(","))]
    return tasks


def hms(secs):
    """Seconds as H:MM:SS, with hours past 24 (a full suite can run for days)."""
    secs = int(secs)
    return f"{secs // 3600}:{secs % 3600 // 60:02}:{secs % 60:02}"


def estimate(agents, tiers, repeat, refs):
    """Project tokens and wall time for a run, from recorded results.

    Token counts are model-agnostic, so they are averaged per agent per tier
    from older results; price them with `cost_of` for whatever model you are
    about to run. Input, cache hits and output are tracked separately so the
    estimate reflects the cache. Seconds come from the same runs. An agent or
    tier with no history falls back to the cross-agent mean for that tier.
    """
    import statistics as st

    seen = {}  # (agent, tier) -> [[in, out, cached], ...]
    secs = {}  # (agent, tier) -> [seconds]
    for f in refs:
        for r in json.load(open(f)).get("results", []):
            u = r.get("usage") or {}
            key = (r["agent"], tier_of(r["task"]))
            seen.setdefault(key, []).append([u.get("input", 0), u.get("output", 0), u.get("cached", 0)])
            secs.setdefault(key, []).append(r["seconds"])

    def mean(pairs):
        if not pairs:
            return None
        return tuple(st.mean([p[i] for p in pairs]) for i in range(3))

    def usage_avg(t):
        """Cross-agent mean (input, output, cached) for a tier, or None if unseen."""
        return mean([x for (a, tt), v in seen.items() if tt == t for x in v])

    def secs_avg(t):
        vals = [x for (a, tt), v in secs.items() if tt == t for x in v]
        return st.mean(vals) if vals else 0.0

    counts = {t: sum(1 for x in select_tasks([t], None)) for t in tiers}
    rows = []
    for a in agents:
        tin = tout = tcache = tsec = 0.0
        for t in tiers:
            m = mean(seen.get((a, t), [])) or usage_avg(t)
            s = st.mean(secs[(a, t)]) if (a, t) in secs else secs_avg(t)
            n = counts[t] * repeat
            if m:
                tin += m[0] * n
                tout += m[1] * n
                tcache += m[2] * n
            tsec += s * n
        rows.append((a, tin, tout, tcache, tsec))
    return counts, rows


# ------------------------------------------------------------------ isolation
# Every run (one agent, one task, one rep) gets its own root under RUNS:
# the task checkout, a fresh HOME and a TMPDIR, and nothing else. The agent runs
# in an OS sandbox (sandbox-exec on macOS, bubblewrap on Linux) that can read
# only that root, its own install, system and toolchain paths, and can connect
# only to localhost (the model proxy). Afterwards the root is deleted; the
# transcript and the patch are kept. docs/sandbox.md has the details and the
# limits. CHANTO_BENCH_ISOLATION=off turns the sandbox off for debugging: the
# result file records the mode, and --report refuses to tabulate such runs.
ISOLATION_ENV = "CHANTO_BENCH_ISOLATION"
# Whether this process's runs are sandboxed (main sets it from the mode).
OFFLINE = False
# The current run's HOME while its command is being built (see home()).
RUN_HOME = None


def isolation_mode(env=None):
    """'off' when CHANTO_BENCH_ISOLATION=off, otherwise the platform's sandbox."""
    value = (os.environ if env is None else env).get(ISOLATION_ENV, "on").strip().lower()
    if value in ("off", "0", "false", "no"):
        return "off"
    if value not in ("", "on", "1", "true", "yes"):
        sys.exit(f"{ISOLATION_ENV}={value!r}: use on (the default) or off")
    return "sandbox-exec" if sys.platform == "darwin" else "bwrap"


def require_offline_platform():
    if sys.platform == "darwin":
        return
    if sys.platform.startswith("linux") and shutil.which("bwrap") and shutil.which("socat"):
        return
    sys.exit(f"isolation needs macOS (sandbox-exec), or Linux with bubblewrap and socat installed; "
             f"{ISOLATION_ENV}=off runs without it, for debugging only (such results can't be published)")


def offline_hidden():
    """Paths that stay hidden even if a toolchain or install path covers them:
    this repository (tasks' hidden tests, past runs), the Chanto sources, other
    runs' workspaces, and caches that could hold a newer release with the fix
    or the SWE-bench gold patches."""
    return [ROOT, CHANTO_REPO, Path.home() / ".cache/chanto-bench", BENCH_HOME, WORK,
            Path.home() / "Library/Caches/pip", Path.home() / ".cache/pip", Path.home() / ".cache/uv",
            Path.home() / "Library/Caches/uv",
            Path.home() / ".cache/huggingface", Path.home() / "Library/Caches/huggingface",
            Path.home() / ".cache/datasets"]


# Read-only system paths every agent needs (shells, libc, dyld, certificates,
# compilers). Package directories inside them are hidden separately for the
# SWE-bench tasks (see python_package_dirs and the macOS regex).
MACOS_SYSTEM = ["/System", "/usr", "/bin", "/sbin", "/Library", "/Applications/Xcode.app", "/opt/homebrew",
                "/private/etc", "/private/var/db/timezone", "/private/var/db/xcode_select_link",
                "/private/var/select", "/private/var/db/dyld", "/dev"]
LINUX_SYSTEM = ["/usr", "/bin", "/sbin", "/lib", "/lib32", "/lib64", "/libx32", "/etc", "/opt", "/nix/store"]
# Language runtimes installed per user, by version managers. Their own data
# (caches, registries) stays out: only the runtimes.
HOME_TOOLCHAINS = [".volta", ".nvm", ".fnm", ".local/share/fnm", ".bun/bin", ".rustup/toolchains", ".rustup/settings.toml",
                   ".cargo/bin", ".pyenv/versions", ".pyenv/shims", ".pyenv/libexec", ".local/share/uv/python",
                   ".local/share/mise/installs", ".asdf/installs", ".asdf/shims", ".go", "sdk", ".local/go"]
# The runtimes agents and task tests start; each one's install prefix is readable.
RUNTIMES = ["node", "python3", "git", "go", "cargo", "rustc", "bun", "uv"]


def toolchain_dirs():
    """Runtimes outside the system paths, read-only: version-manager installs
    under HOME, the install prefix of each runtime on PATH, and anything listed
    in BENCH_TOOLCHAINS (os.pathsep-separated)."""
    home_dir = Path.home().resolve()
    managed = [(Path.home() / p).resolve() for p in HOME_TOOLCHAINS]
    found = list(managed)
    for name in RUNTIMES:
        exe = shutil.which(name)
        if not exe:
            continue
        real = Path(exe).resolve()
        if any(m == real or m in real.parents for m in managed):
            continue
        # A binary in a shared folder (~/.local/bin, /usr/local/bin) adds only
        # that folder: its parent holds caches and other programs' data.
        prefix = real.parent.parent
        broad = prefix in (Path("/"), home_dir, home_dir / ".local", home_dir / ".cargo") or prefix in home_dir.parents
        found.append(real.parent if broad else prefix)
    found += [Path(p) for p in os.environ.get("BENCH_TOOLCHAINS", "").split(os.pathsep) if p]
    out = []
    for p in found:
        try:
            if p.exists() and p.resolve() not in out:
                out.append(p.resolve())
        except OSError:
            continue
    return out


def user_site_dirs():
    """Per-user Python packages (pip install --user): the data-science tasks
    (DS-1000, EvalPlus) may need pandas or numpy from there."""
    import glob
    pats = [Path.home() / "Library/Python/*/lib/python/site-packages", Path.home() / ".local/lib/python3*/site-packages"]
    return [Path(p).resolve() for pat in pats for p in sorted(glob.glob(str(pat)))]


def agent_installs(agent):
    """The one agent install a run may read: its uv tool environment, the
    standalone binaries directory, or the npm prefix. Other agents' installs
    stay hidden (a Python agent's environment can hold a newer requests or
    flask than the task's)."""
    uv = {"aider": "aider-chat", "openhands": "openhands"}
    if agent in uv:
        return [UV_TOOLS / uv[agent]]
    if agent.startswith("chanto"):
        return []
    if (BIN_DIR / agent).exists():
        return [BIN_DIR]
    if agent in VERSION_CMDS or agent == "cline":
        return [NPM_BIN.parent.parent]
    return []


def python_package_dirs():
    """Installed-package directories (Linux) outside any task venv: a newer pytest
    or sympy there already contains the fix. The agents' own installs stay."""
    import glob
    import site
    pats = ["/usr/lib/python3*/site-packages", "/usr/lib/python3*/dist-packages", "/usr/lib/python3/dist-packages",
            "/usr/local/lib/python3*/site-packages", "/usr/local/lib/python3*/dist-packages",
            str(Path.home() / ".local/lib/python3*/site-packages"),
            str(Path.home() / ".local/share/uv/python/*/lib/python3*/site-packages"),
            str(Path.home() / ".pyenv/versions/*/lib/python3*/site-packages"),
            "/opt/hostedtoolcache/Python/*/*/lib/python3*/site-packages",
            "/opt/*/lib/python3*/site-packages"]
    found = {Path(p).resolve() for pat in pats for p in glob.glob(pat)}
    found |= {Path(p).resolve() for p in [*site.getsitepackages(), site.getusersitepackages()] if Path(p).is_dir()}
    keep = [Path(p).resolve() for p in AGENT_INSTALLS]
    return sorted(p for p in found if p.is_dir() and not any(p == k or k in p.parents for k in keep))


def offline_linux(root, installs, cmd, ports, sock_dir, executable=None, keep_site_packages=False, cwd=None):
    """The Linux counterpart of offline_profile, with bubblewrap: a new, empty
    root filesystem with only system and toolchain paths (read-only), the
    agent's install (read-only) and the run root (writable) mounted; no network
    except the listed localhost ports, bridged in over Unix sockets."""
    # Own network, PID and IPC namespaces: when the agent exits, everything it
    # (and the bridges) left behind goes too.
    args = ["bwrap", "--die-with-parent", "--unshare-net", "--unshare-pid", "--unshare-ipc",
            "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp", "--tmpfs", "/var/tmp"]
    ro = []
    for p in LINUX_SYSTEM:
        path = Path(p)
        if path.is_symlink():
            # /bin -> usr/bin on merged-/usr systems: keep it a link.
            args += ["--symlink", os.readlink(path), p]
        elif path.exists():
            ro.append(path)
    ro += toolchain_dirs()
    if keep_site_packages:
        ro += user_site_dirs()
    for p in ro:
        args += ["--ro-bind", str(p), str(p)]
    # Hidden paths that a mounted tree happens to contain, and installed
    # Python packages (they hold newer releases with the fix).
    mounted = [Path(p).resolve() for p in ro]
    hidden = [Path(p).resolve() for p in offline_hidden() if Path(p).exists()]
    if not keep_site_packages:
        hidden += python_package_dirs()
    for p in [h for h in hidden if any(m == h or m in h.parents for m in mounted)]:
        args += ["--tmpfs", str(p)]
    # Later mounts win: the agent's install, its binary and the run root, even under hidden paths.
    for p in installs:
        if Path(p).exists():
            args += ["--ro-bind", str(Path(p).resolve()), str(Path(p).resolve())]
    if executable is not None:
        args += ["--ro-bind", str(executable), str(executable)]
    args += ["--bind", str(Path(root).resolve()), str(Path(root).resolve()),
             "--bind", str(Path(sock_dir).resolve()), str(Path(sock_dir).resolve())]
    sock_dir = Path(sock_dir).resolve()
    bridges = "".join(f"socat TCP-LISTEN:{port},bind=127.0.0.1,fork,reuseaddr UNIX-CONNECT:{sock_dir}/{port}.sock </dev/null >/dev/null 2>&1 & " for port in ports)
    return args + ["--chdir", str(Path(cwd or root).resolve()), "--", "sh", "-c", bridges + 'sleep 0.3; exec "$@"', "sh", *cmd]


def offline_ports():
    """Localhost ports agents talk to: the proxy and meter, or Ollama."""
    from urllib.parse import urlparse
    urls = [u for u in (API, METER) if u] or ["http://localhost:11434"]
    return sorted({urlparse(u).port or 80 for u in urls})


def offline_profile(root, installs=(), executable=None, keep_site_packages=False):
    """The macOS sandbox profile for one run: reads only from the run root, the
    agent's install, system and toolchain paths; writes only to the run root;
    network only to localhost."""
    q = lambda p: json.dumps(str(Path(p).resolve()), ensure_ascii=False)
    root = Path(root).resolve()
    rules = ["(version 1)", "(allow default)",
             # Only localhost: the model proxy and meter, and servers a task's own
             # tests start. DNS goes through mDNSResponder's socket; no other Unix
             # sockets outside the run root (a Docker socket would be a way out).
             "(deny network*)",
             '(allow network-outbound (remote ip "localhost:*"))',
             '(allow network-bind network-inbound (local ip "localhost:*"))',
             '(allow network-outbound (remote unix-socket (path-literal "/private/var/run/mDNSResponder")))',
             f'(allow network* (remote unix-socket (subpath {q(root)})) (local unix-socket (subpath {q(root)})))',
             # No asking another app (a browser, Script Editor) to fetch or open something.
             "(deny appleevent-send)", "(deny lsopen)",
             # Files: nothing readable or writable unless allowed below. Metadata
             # (stat) stays allowed: path lookups need it, and it shows no contents.
             "(deny file-read-data)", "(deny file-write*)"]
    readable = [*MACOS_SYSTEM, *toolchain_dirs(), *(user_site_dirs() if keep_site_packages else [])]
    rules += [f"(allow file-read-data (subpath {q(p)}))" for p in readable if Path(p).exists()]
    rules.append('(allow file-write* (subpath "/dev"))')
    # Then take back what a system or toolchain path happens to contain: the
    # bench data, and (SWE-bench) every installed Python package outside the
    # task's venv, since a newer pytest or sympy already contains the fix. The
    # public data-science tasks (DS-1000, EvalPlus) need system packages.
    rules += [f"(deny file-read-data file-write* (subpath {q(p)}))" for p in offline_hidden()]
    if not keep_site_packages:
        rules.append('(deny file-read-data file-write* (regex #"/(site|dist)-packages(/|$)"))')
    # Another checkout of this repository holds the same tasks and past runs.
    rules.append(f'(deny file-read-data file-write* (regex #"/({CHECKOUT_NAMES})/(tasks|results)(/|$)"))')
    rules.append(f'(deny file-read-data file-write* (regex #"/({CHECKOUT_NAMES})/swebench-[^/]*\\.json$"))')
    # Later rules win, but only over a rule for the same operation: an allow of
    # file-read* doesn't undo a deny of file-read-data, so name it too.
    rules += [f"(allow file-read* file-read-data (subpath {q(p)}))" for p in installs]
    if executable is not None:
        rules.append(f"(allow file-read* file-read-data (literal {q(executable)}))")
    rules.append(f"(allow file-read* file-read-data file-write* (subpath {q(root)}))")
    # getcwd needs to list each parent directory (macOS 26); listing one shows
    # names only, and no sibling run's contents.
    rules += [f"(allow file-read-data (literal {q(a)}))" for a in sorted(root.parents)]
    return "\n".join(rules)


@contextmanager
def offline(agent, cmd, root, keep_site_packages=False, agent_home=None, cwd=None):
    """Wrap an agent command in the platform's sandbox for one run root."""
    require_offline_platform()
    agent_home = Path(agent_home) if agent_home is not None else home("chanto" if agent.startswith("chanto") else agent)
    config = agent_home / "config.toml"
    previous = None
    if agent.startswith("chanto"):
        previous = config.read_bytes() if config.exists() else None
    try:
        if agent.startswith("chanto"):
            # The outer sandbox applies to Chanto and its tools too.
            config.write_text("[sandbox]\nenabled = false\n")
        executable = CHANTO_BIN.resolve() if agent.startswith("chanto") else None
        installs = agent_installs(agent)
        if sys.platform == "darwin":
            yield ["sandbox-exec", "-p", offline_profile(root, installs, executable, keep_site_packages), *cmd]
        else:
            # Each allowed port gets a Unix socket outside, bridged to localhost.
            sock_dir = Path(tempfile.mkdtemp(prefix="net-", dir=root))
            ports = offline_ports()
            bridges = [subprocess.Popen(["socat", f"UNIX-LISTEN:{sock_dir}/{port}.sock,fork,unlink-early", f"TCP:127.0.0.1:{port}"],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for port in ports]
            try:
                time.sleep(0.2)
                yield offline_linux(root, installs, cmd, ports, sock_dir, executable, keep_site_packages, cwd=cwd)
            finally:
                for b in bridges:
                    b.kill()
                shutil.rmtree(sock_dir, ignore_errors=True)
    finally:
        if agent.startswith("chanto"):
            if previous is None:
                config.unlink(missing_ok=True)
            else:
                config.write_bytes(previous)


# Package managers point at nothing: an agent can't fetch a newer release of
# the package under test (the release with the fix) even where the sandbox
# can't stop it, and nothing waits on a network that isn't there.
NO_PACKAGE_INDEX = {
    "PIP_NO_INDEX": "1", "PIP_INDEX_URL": "http://127.0.0.1:9/no-index", "PIP_EXTRA_INDEX_URL": "",
    "PIP_FIND_LINKS": "", "PIP_CONFIG_FILE": os.devnull, "PIP_DISABLE_PIP_VERSION_CHECK": "1",
    "UV_OFFLINE": "1", "UV_NO_CONFIG": "1", "UV_INDEX_URL": "http://127.0.0.1:9/no-index",
    "UV_DEFAULT_INDEX": "http://127.0.0.1:9/no-index",
    "npm_config_registry": "http://127.0.0.1:9/no-index", "npm_config_offline": "true",
    "GOPROXY": "off", "GOFLAGS": "-mod=mod", "CARGO_NET_OFFLINE": "true",
    "HF_HUB_OFFLINE": "1", "HF_DATASETS_OFFLINE": "1",
}


def new_run_root(agent, task, rep):
    """A fresh, private root for one run: <root>/<task>-<rep> (the checkout),
    <root>/home and <root>/tmp. The name is random, so a run can't guess where
    another one lives."""
    RUNS.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="r-", dir=RUNS)).resolve()
    for d in ("home", "tmp"):
        (root / d).mkdir(mode=0o700)
    return root


def real_node_dir():
    """The folder of the node binary behind a version-manager shim (Volta),
    put first on PATH: the shim reads its own state and any package.json above
    the workspace, which the sandbox hides, and then refuses to start."""
    node = shutil.which("node")
    if not node or Path(node).resolve().name != "volta-shim" or not shutil.which("volta"):
        return None
    try:
        real = subprocess.run(["volta", "which", "node"], capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None
    return str(Path(real).parent) if real and Path(real).exists() else None


def run_env(root, extra_env):
    """The environment an agent runs with: a fresh HOME, XDG dirs and TMPDIR
    in its run root, no package index, a neutral git identity, and the real
    locations of runtimes that a version manager would otherwise look for in
    the (new) HOME."""
    env = dict(os.environ)
    real = Path.home()
    for var, path in (("RUSTUP_HOME", real / ".rustup"), ("VOLTA_HOME", real / ".volta"), ("NVM_DIR", real / ".nvm"),
                      ("PYENV_ROOT", real / ".pyenv")):
        if var not in env and path.exists():
            env[var] = str(path)
    h = root / "home"
    env.update({"HOME": str(h), "USERPROFILE": str(h), "XDG_CONFIG_HOME": str(h / ".config"),
                "XDG_DATA_HOME": str(h / ".local/share"), "XDG_STATE_HOME": str(h / ".local/state"),
                "XDG_CACHE_HOME": str(h / ".cache"), "CARGO_HOME": str(h / ".cargo"), "GOPATH": str(h / "go"),
                "GOMODCACHE": str(h / "go/pkg/mod"), "TMPDIR": str(root / "tmp"), "TMP": str(root / "tmp"),
                "TEMP": str(root / "tmp"), "GIT_CONFIG_NOSYSTEM": "1",
                # Tools that keep sockets or scratch under /tmp/<name>-<uid> by default.
                "TMUX_TMPDIR": str(root / "tmp"), "CLAUDE_CODE_TMPDIR": str(root / "tmp"),
                "XDG_RUNTIME_DIR": str(root / "tmp"),
                "GIT_AUTHOR_NAME": "bench", "GIT_AUTHOR_EMAIL": "bench@localhost",
                "GIT_COMMITTER_NAME": "bench", "GIT_COMMITTER_EMAIL": "bench@localhost"})
    for k in ("PIP_REQUIRE_VIRTUALENV", "PYTHONUSERBASE", "PYTHONPATH", "PYTHONSTARTUP", "VIRTUAL_ENV"):
        env.pop(k, None)
    node_dir = real_node_dir()
    if node_dir:
        env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")
    env.update(NO_PACKAGE_INDEX)
    env.update(extra_env)
    return env


def seal_checkout(wd):
    """Leave the checkout's git history ending at the task's starting point:
    no remotes, alternates, other refs, reflogs or unreachable objects, so
    `git log --all`, `git fsck --lost-found` or `git cat-file
    --batch-all-objects` find nothing from the future. Fails the run's setup
    if anything is left."""
    git = lambda *a: subprocess.run(["git", "-C", str(wd), *a], capture_output=True, text=True, timeout=600)
    dot = Path(wd) / ".git"
    if not dot.is_dir():
        raise RuntimeError(f"{wd}: no .git directory to seal")
    for remote in git("remote").stdout.split():
        git("remote", "remove", remote)
    head = git("symbolic-ref", "-q", "HEAD").stdout.strip()
    for ref in git("for-each-ref", "--format=%(refname)").stdout.split():
        if ref != head:
            git("update-ref", "-d", ref)
    for name in ("objects/info/alternates", "FETCH_HEAD", "ORIG_HEAD", "MERGE_HEAD", "packed-refs.lock", "shallow"):
        (dot / name).unlink(missing_ok=True)
    git("reflog", "expire", "--expire=now", "--all")
    gc = git("-c", "gc.reflogExpire=now", "-c", "gc.reflogExpireUnreachable=now", "-c", "gc.pruneExpire=now",
             "gc", "--prune=now", "--quiet")
    if gc.returncode:
        raise RuntimeError(f"git gc failed in {wd}: {gc.stderr[-500:]}")
    reachable = set(git("rev-list", "--objects", "--all").stdout.split())
    stored = git("cat-file", "--batch-all-objects", "--batch-check=%(objectname)").stdout.split()
    extra = [o for o in stored if o not in reachable]
    commits = git("rev-list", "--all").stdout.split()
    if extra or git("remote").stdout.strip() or (dot / "objects/info/alternates").exists():
        raise RuntimeError(f"{wd}: git still holds {len(extra)} objects past the task's starting point")
    return {"commits": len(commits), "objects": len(stored)}


def prefetch(wd, env):
    """Download a task's declared Rust dependencies into the run's own
    CARGO_HOME before the agent starts: the sandbox has no network, and the
    shared ~/.cargo stays out of reach."""
    cargo = Path(wd) / "Cargo.toml"
    if cargo.exists() and re.search(r"^\[(dev-)?dependencies\]\s*\n\s*[A-Za-z_]", cargo.read_text(), re.M) and shutil.which("cargo"):
        fetch_env = {k: v for k, v in env.items() if k not in NO_PACKAGE_INDEX}
        subprocess.run(["cargo", "fetch", "--quiet"], cwd=wd, env=fetch_env, capture_output=True, timeout=600)


# Off-task access: what a transcript shows an agent reaching for that isn't
# its task. The sandbox blocks most of it; recording the attempts makes
# contamination visible where it can't be blocked, and on runs without it.
OFFTASK_PATTERNS = [
    ("bench data", re.compile(r"chanto-bench|work-hard-[\w-]*|harness-verify|/\.homes/|/runs/r-\w{8}\b")),
    ("package download", re.compile(r"\bpip3?\s+download\b|\bpip3?\s+index\b|\bpip3?\s+install\s+[^\n]*(?:-U\b|--upgrade\b)"
                                    r"|\buv\s+pip\s+install\b|\bpip3?\s+install\s+[^\n]*(?:git\+|https?://)")),
    ("package host", re.compile(r"(?:pypi\.org|files\.pythonhosted\.org)[^\s\"'\\]*")),
    ("git history", re.compile(r"\bgit\s+(?:--?[\w.=-]+\s+(?:[^\s-]\S*\s+)?){0,4}(?:fsck|fetch|clone|pull)\b[^\n]{0,160}|--lost-found|--batch-all-objects"
                               r"|\bgit\s+remote\s+add\b|\bgit\s+(?:log|rev-list)\s+[^\n]*--(?:all|reflog)\b")),
    ("whole-disk search", re.compile(r"\b(?:find|fd|rg|grep\s+-[a-zA-Z]*r[a-zA-Z]*|ls\s+-[a-zA-Z]*R[a-zA-Z]*|du)\s+/(?:\s|$|\"|')"
                                     r"|\bmdfind\b|\blocate\s")),
    # The fix itself on GitHub: a pull request, commit, compare view or patch,
    # or anything from its API. The upstream repository's own URLs are added
    # per task (see offtask_hits).
    ("web", re.compile(r"(?:https?://)?github\.com/[\w.-]+/[\w.-]+/(?:pull|commit|compare|blob|tree|raw)/[^\s\"'\\)]+"
                       r"|api\.github\.com[^\s\"'\\)]*|patch-diff\.githubusercontent\.com[^\s\"'\\)]*")),
]
# What agents fetch for themselves at startup (skills, model price lists),
# blocked by the sandbox and not about the task.
AGENT_SELF_FETCH = ("OpenHands/extensions", "BerriAI/litellm")
# Absolute paths that are expected outside the run root: system and toolchain locations.
OFFTASK_PATH = re.compile(r"(?<![\w.~/-])(/(?:Users|home|root|private|tmp|var|opt|mnt|Volumes|srv|data)/[^\s\"'`:;,)\]}>|\\]+)")
# Scratch space (/tmp) counts as expected: agents write scratch files there all
# the time, and the sandbox gives it no contents worth reading.
OFFTASK_PACKAGES = re.compile(r"(?<![\w.~/-])(/[^\s\"'`:;,)\]}>|\\]*/(?:site|dist)-packages/[^\s\"'`:;,)\]}>|\\]+)")
EXPECTED_PATHS = ("/private/etc", "/private/var/folders", "/var/folders", "/opt/homebrew", "/opt/hostedtoolcache",
                  "/tmp", "/private/tmp", "/var/tmp", "/private/var/tmp", "/var/run/mDNSResponder")


def offtask_hits(texts, root, task=None, prompt="", limit=50):
    """Off-task access in a run's transcripts: absolute paths outside the run
    root (and outside system and toolchain paths), package downloads, git
    history beyond the task's base, whole-disk searches, and GitHub URLs
    (the upstream repository or its fix). URLs the task's own prompt quotes
    don't count. Returns up to `limit` distinct (kind, text) hits."""
    root = str(Path(root).resolve()) if root else None
    allowed = [str(p) for p in toolchain_dirs()] + list(EXPECTED_PATHS)
    allowed += [str(Path(p).resolve()) for p in AGENT_INSTALLS]
    patterns = list(OFFTASK_PATTERNS)
    instance = TASKS / task / "instance.json" if task else None
    if instance is not None and instance.exists():
        # A SWE-bench task's upstream repository, under any GitHub URL.
        repo = json.loads(instance.read_text()).get("repo", "")
        if repo:
            patterns.append(("upstream repo", re.compile(r"(?:github\.com|githubusercontent\.com)/" + re.escape(repo) + r"\b[^\s\"'\\)]*", re.I)))
    hits, seen = [], set()

    def add(kind, text):
        text = text.strip()[:200]
        if (kind, text) not in seen and len(hits) < limit:
            seen.add((kind, text))
            hits.append({"kind": kind, "text": text})

    for text in texts:
        # Some agents print the run's own long path wrapped over two lines.
        # `flat` joins wrapped lines back up, so the root can be taken out of
        # it too; a hit found in the text only counts if it's still there, at
        # the start of a path, once the root is gone.
        flat = re.sub(r"[ \t]*\n[ \t│|]*", "", text)
        if root:
            # The run's own root is on task; take it out before looking.
            text, flat = (t.replace(root, "RUNROOT").replace(root.removeprefix("/private"), "RUNROOT") for t in (text, flat))
        starts_path = lambda p: re.search(r"(?<![\w.~/-])" + re.escape(p), flat) is not None
        for kind, pat in patterns:
            # git commands are read joined up: the URL a clone names can be on the next line.
            for m in pat.finditer(flat if kind == "git history" else text):
                s = m.group(0)
                if any(n in s for n in AGENT_SELF_FETCH):
                    continue
                if kind in ("web", "upstream repo") and s.rstrip(".") in prompt:
                    continue
                if kind == "bench data" and s not in flat:
                    continue
                add(kind, s)
        # Installed packages outside the task's venv (an agent's own
        # environment included) can hold a newer release with the fix.
        for m in OFFTASK_PACKAGES.finditer(text):
            if starts_path(m.group(1)):
                add("installed package", m.group(1))
        for m in OFFTASK_PATH.finditer(text):
            p = m.group(1).rstrip(".")
            if "-packages/" in p or not starts_path(p) or p in prompt:
                continue
            if any(p == a or p.startswith(a.rstrip("/") + "/") for a in allowed):
                continue
            add("path outside run root", p)
    return hits


def kill_process_group(p):
    """Clean up children still in the original group, not detached sessions."""
    try:
        os.killpg(p.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        # The group is gone, or the pid was reused by something we may not
        # signal. Neither is a reason to abort the shard.
        pass


def kill_leftovers(wd):
    """Kill processes still working in `wd` after the agent is gone: test
    runs an agent started in their own process group outlive a SIGKILL of the
    agent's group, and an orphaned test suite can run for hours and load the
    machine for every later task."""
    try:
        out = subprocess.run(["lsof", "-a", "-d", "cwd", "-F", "pn"], capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return
    pid, root = None, str(wd)
    for line in out.splitlines():
        if line.startswith("p"):
            pid = int(line[1:])
        elif line.startswith("n") and pid and pid != os.getpid() and (line[1:] == root or line[1:].startswith(root + os.sep)):
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass


def reap(p, grace=10):
    """Stop a run that overran its deadline and reap it — but never wait on a
    process that refuses to die.

    A process blocked in a kernel call (a stuck network read, say) does not
    become reapable the moment it is sent SIGKILL. Waiting it out without a
    bound once recorded 49 minutes against a 5-minute limit and stalled every
    later task in the shard.
    """
    kill_process_group(p)
    if p.poll() is None:
        try:
            p.kill()
        except (ProcessLookupError, PermissionError):
            pass
    try:
        p.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        pass  # leave it; it is already detached and will be reaped by init


def run_check(cmd, wd, env, timeout=300):
    """Grade a task, with a deadline and cleanup of its original process group."""
    p = subprocess.Popen(cmd, cwd=wd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        out, err = p.communicate(timeout=timeout)
        return subprocess.CompletedProcess(cmd, p.returncode, out, err)
    except subprocess.TimeoutExpired:
        kill_process_group(p)
        try:
            out, err = p.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            out, err = "", ""
        return subprocess.CompletedProcess(cmd, 124, out, (err or "") + f"\n[check timed out after {timeout}s]")
    finally:
        reap(p)


def deepseek_balance():
    """Remaining USD balance on the DeepSeek account (None if unknown)."""
    import urllib.request
    try:
        key = (Path.home() / ".config/chanto-bench/deepseek_key").read_text().strip()
        req = urllib.request.Request("https://api.deepseek.com/user/balance", headers={"Authorization": f"Bearer {key}"})
        data = json.load(urllib.request.urlopen(req, timeout=15))
        return sum(float(b["total_balance"]) for b in data["balance_infos"] if b["currency"] == "USD")
    except Exception:
        return None


def prepare_task(tdir, wd):
    """Set up the repository before starting the agent's clock."""
    hook = tdir / "setup.sh"
    # Setup occasionally fails transiently (e.g. ensurepip), so retry once from a clean copy.
    for attempt in range(2):
        shutil.rmtree(wd, ignore_errors=True)
        shutil.copytree(tdir / "files", wd)
        if not hook.exists():
            return
        result = run_check(["nice", "-n", "19", "bash", str(hook)], wd, dict(os.environ), 600)
        if not result.returncode:
            return
    raise RuntimeError(f"Setup failed for {tdir.name}: {result.stdout[-2000:]}{result.stderr[-2000:]}")


def sandbox_name():
    """The isolation mode this process's runs use, as recorded in results."""
    return ("sandbox-exec" if sys.platform == "darwin" else "bwrap") if OFFLINE else "off"


def run_task(agent, task, model, ctx, timeout, rep):
    if OFFLINE:
        require_offline_platform()
    tdir = TASKS / task
    prompt = (tdir / "prompt.txt").read_text().strip()
    # The run's own root: checkout, HOME and TMPDIR, deleted afterwards. The
    # transcript and the patch are kept next to the other runs' in WORK/<agent>.
    root = new_run_root(agent, task, rep)
    wd = root / f"{task}-{rep}"
    logs = WORK / agent
    logs.mkdir(parents=True, exist_ok=True)
    out_file = logs / f"{task}-{rep}.out"
    keep_root = bool(os.environ.get("BENCH_KEEP_WORK"))
    try:
        return _run_in_root(agent, task, model, ctx, timeout, rep, tdir, prompt, root, wd, out_file)
    finally:
        if not keep_root and not KEEP_ROOTS.pop(str(root), False):
            subprocess.run(["chmod", "-R", "u+rwx", str(root)], capture_output=True)
            shutil.rmtree(root, ignore_errors=True)


# Run roots kept for inspection because their evidence couldn't be saved.
KEEP_ROOTS = {}


def _run_in_root(agent, task, model, ctx, timeout, rep, tdir, prompt, root, wd, out_file):
    global API, RUN_HOME
    prepare_task(tdir, wd)
    for step in (["init", "-q"], ["add", "-A"], ["-c", "user.email=b@b", "-c", "user.name=bench", "commit", "-qm", "init"]):
        subprocess.run(["git", *step], cwd=wd, capture_output=True)
    # Nothing past the task's starting point: no remotes, other refs or loose objects.
    seal_checkout(wd)
    tests_before = test_files(wd)
    agent_home = root / "home"
    label = None
    if METER:
        import uuid
        label = f"{agent}~{task}~{rep}~{uuid.uuid4().hex[:8]}"
        saved_api, API = API, f"{METER}/{label}"
    RUN_HOME = agent_home
    try:
        cmd, extra_env = agent_cmd(agent, model, prompt, ctx, wd)
    finally:
        RUN_HOME = None
        if METER:
            API = saved_api
    if METER and agent == "goose":
        # Goose takes a host plus a separate path.
        extra_env["OPENAI_HOST"] = METER
        extra_env["OPENAI_BASE_PATH"] = f"{label}/v1/chat/completions"
    env = run_env(root, extra_env)
    if (wd / ".venv/bin").exists():
        env["VIRTUAL_ENV"] = str(wd / ".venv")
        env["PATH"] = str(wd / ".venv/bin") + os.pathsep + env["PATH"]
    env["PWD"] = str(wd)  # some agents resolve their project from $PWD, not the process cwd
    if agent == "claude":
        env.pop("ANTHROPIC_API_KEY", None)
    if API:
        # Hosted runs must not leak real provider keys from the environment.
        for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "MISTRAL_API_KEY", "GROQ_API_KEY"):
            if k not in extra_env:
                env.pop(k, None)
    prefetch(wd, env)
    t0 = time.time()
    timed_out = False
    keep_site_packages = not task.startswith("swe-")
    sandbox = offline(agent, cmd, root, keep_site_packages, agent_home=agent_home, cwd=wd) if OFFLINE else nullcontext(cmd)
    with sandbox as cmd, open(out_file, "w") as f:
        # Detached children that create their own process group are not covered.
        p = subprocess.Popen(cmd, cwd=wd, env=env, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                             start_new_session=True)
        try:
            code = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            code = -1
            timed_out = True
        # Stop the clock at the deadline, before cleanup. Reaping a process that
        # is slow to die is not the task's fault and must not be billed to it.
        elapsed = time.time() - t0
        reap(p)
        kill_leftovers(root)
        # Let an agent's own cleanup after a kill (Chanto's put-back guard)
        # land before the diff is taken.
        time.sleep(1)
    ended = time.time()
    # Before the check runs: it may apply the hidden tests to the workspace.
    patch = workspace_diff(wd)
    out_file.with_suffix(".patch").write_bytes(patch)
    check_env = dict(os.environ, OUTPUT_FILE=str(out_file))
    envf = tdir / "env"
    if envf.exists():
        for line in envf.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                check_env[k.strip()] = v.strip()
    after = test_files(wd)
    chk = run_check(["bash", str(tdir / "check.sh")], wd, check_env, timeout=600 if task.startswith("swe-") else 300)
    passed = chk.returncode == 0
    tampered = sorted(f for f, h in tests_before.items() if after.get(f) != h)
    # What the agent said about its own run: "done, and it works", "I errored",
    # or unknown when it prints no structured signal (see completion_status).
    claimed_done, errored = completion_status(agent, timed_out, out_file)
    # It reported success, and the grader disagrees that it works.
    false_done = claimed_done is True and not passed
    # The old, agent-agnostic proxy — a clean exit that still failed — kept so a
    # run on a signal-less agent can still be flagged, just not as a claim.
    clean_exit_fail = code == 0 and not timed_out and not passed
    tokens = None
    if agent.startswith("chanto") or agent == "claude":
        try:
            last = [l for l in out_file.read_text().splitlines() if l.strip().startswith("{")][-1]
            j = json.loads(last)
            u = j.get("usage", {})
            # Chanto's input_tokens is OpenAI-style: the whole prompt, cache
            # hits included. Claude's excludes cache reads, so add them back to
            # compare like for like.
            inp = u.get("input_tokens")
            if inp is not None and agent == "claude":
                inp += (u.get("cache_read_input_tokens") or 0) + (
                    u.get("cache_creation_input_tokens") or 0
                )
            tokens = {"in": inp, "out": u.get("output_tokens")}
            if u.get("cached_tokens") is not None:
                tokens["cached"] = u["cached_tokens"]
        except Exception:
            pass
    try:
        sessions = session_files(agent_home, t0)
    except Exception:
        sessions = []
    leaked = test_leak(task, rep, out_file, sessions)
    texts = []
    for f in [out_file, *sessions]:
        try:
            texts.append(Path(f).read_text(errors="ignore"))
        except OSError:
            pass
    hits = offtask_hits(texts, root, task, prompt)
    evidence = keep_evidence(agent, task, rep, out_file, patch, chk, sessions)
    if "error" in evidence:
        # The evidence couldn't be saved: keep the root to recover it by hand.
        KEEP_ROOTS[str(root)] = True
    return {
        "agent": agent, "task": task, "rep": rep, "passed": passed, "seconds": round(elapsed, 1),
        # Which `[optimize]` switches were on (full key names), for chanto agents.
        "optimize": [OPTIMIZE_FLAGS[n] for n in chanto_optimizations(agent)] if agent.startswith("chanto") else None,
        "exit_code": code, "timed_out": timed_out, "check_output": chk.stdout[-800:] + chk.stderr[-400:],
        "tokens": tokens, "tampered": tampered, "false_done": false_done,
        "leaked": leaked,
        # How the run was isolated, and what its transcript shows it reaching
        # for outside its task anyway (see offtask_hits).
        "isolation": sandbox_name(),
        "offtask_hits": hits,
        "claimed_done": claimed_done, "errored": errored, "clean_exit_fail": clean_exit_fail,
        "usage": metered(label),
        # Matches this run's lines in the meter log (every model call it made).
        "meter_label": label,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(t0)),
        "ended_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(ended)),
        "evidence": evidence,
    }


# Evidence kept next to each result file (results/<stem>/), so a skeptical
# reader can check every number instead of trusting the table: what ran
# (versions, binary and task hashes, the sandbox profile), what each agent did
# (its full output and the change it made) and what the grader printed.
ARTIFACTS = None

VERSION_CMDS = {
    **{a: [agent_exe(a), "--version"] for a in ("claude", "codex", "opencode", "goose", "aider", "openhands",
                                                 "codewhale", "zerostack", "hax")},
    "pi": [str(NPM_BIN / "pi"), "--version"], "crush": [str(NPM_BIN / "crush"), "--version"],
    "qwen": [str(NPM_BIN / "qwen"), "--version"], "kilo": [str(NPM_BIN / "kilo"), "--version"],
    "forge": [str(NPM_BIN / "forge"), "--version"],
    "cline": [str(CLINE_BIN), "--version"],
    "cn": [str(NPM_BIN / "cn"), "--version"],
    "gemini": [str(NPM_BIN / "gemini"), "--version"],
}


def first_line(cmd, timeout=60):
    """A command's first line of output, or why it couldn't run."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        lines = (r.stdout.strip() or r.stderr.strip()).splitlines()
        return lines[0][:200] if lines else f"no output (exit {r.returncode})"
    except Exception as e:
        return f"unavailable: {e}"[:200]


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def task_digest(task):
    """Hash of a task's definition (prompt, setup, check, test patch, starter files)."""
    h = hashlib.sha256()
    # Bytecode left by a local check run isn't part of the task.
    for f in sorted(p for p in (TASKS / task).rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        h.update(str(f.relative_to(TASKS / task)).encode() + b"\0")
        h.update(f.read_bytes())
    return h.hexdigest()


def run_meta(args, tasks):
    """Everything needed to rerun this exactly, or to spot what differed."""
    import platform
    git = lambda *a: first_line(["git", "-C", str(ROOT), *a])
    agents = args.agents.split(",")
    versions = {}
    for a in agents:
        if a.startswith("chanto"):
            versions[a] = first_line([str(CHANTO_BIN), "--version"])
        elif a in VERSION_CMDS:
            versions[a] = first_line(VERSION_CMDS[a])
    meta = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "command": [Path(sys.argv[0]).name, *sys.argv[1:]],
        "bench_commit": git("rev-parse", "HEAD"),
        # Uncommitted changes to the benchmark itself (tasks, runner, grader) at run time.
        "bench_dirty": bool(subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", ".", ":(exclude)results"],
                                           capture_output=True, text=True).stdout.strip()),
        # The Chanto sources the binary was built from, when the checkout is there.
        "chanto_commit": first_line(["git", "-C", str(CHANTO_REPO), "rev-parse", "HEAD"]) if CHANTO_REPO.is_dir() else None,
        "chanto_bin": {"path": str(CHANTO_BIN), "sha256": sha256_of(CHANTO_BIN) if CHANTO_BIN.exists() else None},
        "agent_versions": versions,
        # Experimental optimizations each chanto agent ran with, and the shared effort.
        "chanto_optimize": {a: [OPTIMIZE_FLAGS[n] for n in chanto_optimizations(a)] for a in agents if a.startswith("chanto")},
        "chanto_effort": CHANTO_EFFORT,
        "model_alias": args.model,
        # What the proxy actually sends the alias to (e.g. deepseek/deepseek-flash).
        "upstream_model": upstream_model(args.model) if API else None,
        "proxy": first_line(["litellm", "--version"]) if API else None,
        "platform": {"system": platform.platform(), "machine": platform.machine(), "cpus": os.cpu_count(), "python": platform.python_version()},
        "offline_sandbox": OFFLINE,
        # How every run in this file was isolated: sandbox-exec, bwrap or off.
        "isolation": sandbox_name(),
        "timeout_s": args.timeout,
        "seed": args.seed,
        "repeat": args.repeat,
        "tasks": {t: task_digest(t) for t in tasks},
    }
    if OFFLINE and sys.platform == "darwin":
        both = (offline_profile(WORK / "runs/PROFILE") + offline_profile(WORK / "runs/PROFILE", keep_site_packages=True))
        meta["offline_profile_sha256"] = hashlib.sha256(both.encode()).hexdigest()
    return meta


def hosted_context(alias):
    """The context window of the model behind the proxy alias, as LiteLLM
    reports it, so every agent is given the model's real window."""
    import urllib.request
    try:
        req = urllib.request.Request(f"{API}/model/info", headers={"Authorization": f"Bearer {API_KEY}"})
        data = json.load(urllib.request.urlopen(req, timeout=15))
    except Exception as e:
        sys.exit(f"couldn't ask the proxy for {alias}'s context window ({e}); pass --ctx")
    info = next((m.get("model_info") or {} for m in data.get("data", []) if m.get("model_name") == alias), {})
    ctx = info.get("max_input_tokens") or info.get("max_tokens")
    if not ctx:
        sys.exit(f"the proxy doesn't know {alias}'s context window; pass --ctx")
    return int(ctx)


def upstream_model(alias):
    """Ask the LiteLLM proxy which provider model the alias is routed to."""
    import urllib.request
    try:
        req = urllib.request.Request(f"{API}/model/info", headers={"Authorization": f"Bearer {API_KEY}"})
        data = json.load(urllib.request.urlopen(req, timeout=15))
        return next((m["litellm_params"]["model"] for m in data.get("data", []) if m.get("model_name") == alias), None)
    except Exception as e:
        return f"unavailable: {e}"[:200]


def workspace_diff(wd, exclude=()):
    """The change an agent made, new files included, without touching the repo's
    own index. Diffs against the workspace's first commit (the bench's "init"),
    so an agent that commits its own work still shows all of it."""
    index = Path(wd) / ".git" / "bench-diff-index"
    env = dict(os.environ, GIT_INDEX_FILE=str(index))
    git = lambda *a: subprocess.run(["git", *a], cwd=wd, env=env, capture_output=True, timeout=300)
    try:
        roots = git("rev-list", "--max-parents=0", "HEAD").stdout.split()
        if len(roots) != 1:
            return b"diff unavailable: the workspace's history no longer starts at the bench's init commit\n"
        base = roots[0].decode()
        for step in (("read-tree", base), ("add", "-A", "--", ".")):
            r = git(*step)
            if r.returncode:
                return f"diff unavailable: git {step[0]} failed: {r.stderr.decode(errors='replace')[:300]}\n".encode()
        # Build and test output isn't the agent's change (no task ships a .gitignore).
        noise = ["target", "node_modules", ".venv", "**/__pycache__", "**/*.pyc", ".pytest_cache", "**/.pytest_cache", ".mypy_cache", ".ruff_cache"]
        r = git("diff", "--cached", "--binary", base, "--", ".", *[f":(exclude){f}" for f in [*noise, *exclude]])
        return r.stdout if r.returncode == 0 else f"diff unavailable: {r.stderr.decode(errors='replace')[:300]}\n".encode()
    except Exception as e:
        return f"diff unavailable: {e}\n".encode()
    finally:
        index.unlink(missing_ok=True)


def session_files(agent_home, since):
    """The agent's own step-by-step transcripts written during this run (Chanto
    sessions, Claude Code and Codex JSONL, ...): whatever session-like files in
    its home changed since the run began. Runs in a shard are sequential, so
    they're this run's."""
    found = []
    for p in Path(agent_home).rglob("*"):
        try:
            st = p.stat()
        except OSError:
            continue
        session = p.suffix == ".jsonl" or (p.suffix == ".json" and "sessions" in p.parts)
        if p.is_file() and session and st.st_mtime >= since and st.st_size < 20_000_000:
            found.append(p)
    return sorted(found)


def test_leak(task, rep, out_file, sessions=()):
    """Whether this cell's transcript names the task's hidden tests.

    Online runs leave the checkout readable, so an agent that finds
    `tasks/<task>/pristine/test.py` can read what it will be graded on and
    tune to it (cline did exactly that on mbpp-597). The score stays honest only
    if that's visible, so record it with the cell.
    """
    needles = (f"tasks/{task}", "pristine/test")
    try:
        text = out_file.read_text(errors="ignore")
    except OSError:
        text = ""
    if any(n in text for n in needles):
        return True
    # Some agents append every session to one log, so a session line only
    # counts for this cell if it also names this cell's workspace.
    own = f"{task}-{rep}"
    for f in sessions:
        try:
            lines = f.read_text(errors="ignore").splitlines()
        except OSError:
            continue
        if any(own in line and any(n in line for n in needles) for line in lines):
            return True
    return False


def redact(data):
    """Published results show `~` for the home directory and no user name
    (pytest's temp dirs carry it), for str or bytes."""
    home, user = str(Path.home()), getpass.getuser()
    if isinstance(data, bytes):
        return data.replace(home.encode(), b"~").replace(f"pytest-of-{user}".encode(), b"pytest-of-user")
    return data.replace(home, "~").replace(f"pytest-of-{user}", "pytest-of-user")


def keep_evidence(agent, task, rep, out_file, patch, chk, sessions=()):
    """Copy a run's transcript, diff and full grader output next to the results."""
    if ARTIFACTS is None:
        return {}
    try:
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        stem = f"{agent}~{task}~{rep}"
        files = {
            "transcript": (ARTIFACTS / f"{stem}.out", Path(out_file).read_bytes()),
            "patch": (ARTIFACTS / f"{stem}.patch", redact(patch)),
            "check": (ARTIFACTS / f"{stem}.check.txt", (chk.stdout + "\n--- stderr ---\n" + chk.stderr).encode(errors="replace")),
        }
        for i, src in enumerate(sessions):
            files[f"session{i}"] = (ARTIFACTS / f"{stem}.session{i}{src.suffix}", src.read_bytes())
        out = {}
        for k, (path, data) in files.items():
            path.write_bytes(data)
            out[k] = {"file": f"{ARTIFACTS.name}/{path.name}", "sha256": hashlib.sha256(data).hexdigest()}
        return out
    except Exception as e:
        return {"error": str(e)[:200]}


def wilson(k, n, z=1.96):
    """95% confidence interval for a pass rate (Wilson score)."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (c - m) / d), min(1.0, (c + m) / d)


def sign_test(wins, losses):
    """Exact two-sided sign test (McNemar's test for paired pass/fail): the
    chance of a split at least this lopsided if both agents were equally good."""
    n, k = wins + losses, min(wins, losses)
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def paired(results, ref):
    """Each agent against `ref` on the tasks both ran: per task, compare pass
    rates (over repeats) and count who did better."""
    rate = {}
    for r in results:
        rate.setdefault((r["agent"], r["task"]), []).append(bool(r["passed"]))
    rows = []
    for a in dict.fromkeys(r["agent"] for r in results):
        if a == ref:
            continue
        common = sorted(t for (x, t) in rate if x == a and (ref, t) in rate)
        mean = lambda xs: sum(xs) / len(xs)
        better = sum(mean(rate[(ref, t)]) > mean(rate[(a, t)]) for t in common)
        worse = sum(mean(rate[(ref, t)]) < mean(rate[(a, t)]) for t in common)
        rows.append((a, len(common), better, worse, sign_test(better, worse)))
    return rows


def result_event(out_file):
    """The `result` JSON an agent prints when it finishes a print-mode turn
    (chanto and claude both do; see `result_json` in src/main.rs). stream-json
    output carries other JSON lines, so require the marker."""
    try:
        lines = out_file.read_text(errors="replace").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            j = json.loads(line)
        except ValueError:
            continue
        if isinstance(j, dict) and (j.get("type") == "result" or "is_error" in j):
            return j
    return None


def completion_status(agent, timed_out, out_file):
    """(claimed_done, errored): what the agent said about its own run, or
    (None, None) when it prints no structured signal.

    The exit code is deliberately not consulted. It does not mean what reading
    `code == 0` as "it thought it was done" assumes: most agents exit 0 on
    every run, crash or not (forge prints "ERROR: Device not configured" and
    still exits 0), while chanto-verify exits 3 on runs that *pass* and
    opencode exits 1 on some that pass. So read the agent's own words where it
    has them, and admit ignorance where it doesn't.
    """
    if timed_out:
        return None, None
    if agent == "forge":
        # Reports failures in-band, in the transcript stream:
        #   ● [09:34:05] ERROR: Device not configured (os error 6)
        try:
            errored = "ERROR:" in out_file.read_text(errors="replace")
        except OSError:
            return None, None
        return (not errored), errored
    if agent.startswith("chanto") or agent == "claude":
        j = result_event(out_file)
        if j is not None and "is_error" in j:
            errored = bool(j["is_error"])
            return (not errored), errored
    return None, None


def file_isolation(data):
    """How a result file's runs were isolated (sandbox-exec, bwrap), or None
    for runs made without it: CHANTO_BENCH_ISOLATION=off, and every file from
    before isolation was recorded (their --offline sandbox shared one work
    folder and config home between runs)."""
    mode = data.get("isolation") or (data.get("meta") or {}).get("isolation")
    return None if mode in (None, "off") else mode


def report(files, ref="chanto", unisolated=False):
    by_key = {}
    model = ctx = upstream = None
    bare = [f for f in files if file_isolation(json.loads(Path(f).read_text())) is None]
    if bare and not unisolated:
        raise SystemExit("not publishing runs made without isolation (CHANTO_BENCH_ISOLATION=off, or recorded before "
                         "isolation existed): " + ", ".join(map(str, bare)) + "\nRe-run them isolated, or pass --unisolated "
                         "to see them labelled as unisolated.")
    for f in files:
        d = json.loads(Path(f).read_text())
        model, ctx = d.get("model"), d.get("ctx")
        upstream = (d.get("meta") or {}).get("upstream_model") or upstream
        # A run recorded twice (overlapping files) counts once.
        for r in d["results"]:
            r["agent"] = r["agent"]
            by_key[(r["agent"], r["task"], r.get("rep", 0))] = r
    results = list(by_key.values())
    agents = list(dict.fromkeys(r["agent"] for r in results))
    tasks = sorted(set(r["task"] for r in results))
    served = f"`{upstream}` (as `{model}`) through one proxy" if upstream else f"`{model}`, same server"
    out = [f"Model: {served} for all agents · context {ctx}\n"]
    if bare:
        out.insert(0, f"**Measured without isolation** ({len(bare)} of {len(files)} result files): agents could reach other "
                      "runs' workspaces, package caches, upstream history or the network, so these numbers may be inflated. "
                      "Not for publishing.\n")
    # Totals only over tasks every agent ran, so the rates share a denominator.
    complete = [t for t in tasks if all(any(r["agent"] == a and r["task"] == t for r in results) for a in agents)]
    left_out = sum(r["task"] not in complete for r in results)
    if left_out:
        out.append(f"Totals cover the {len(complete)} tasks every agent ran; {left_out} runs on other tasks appear only in the per-task table.\n")
    # Showcase tasks (answers, not code) never count toward the coding score.
    showcase = [t for t in complete if tier_of(t) == "showcase"]
    complete = [t for t in complete if t not in showcase]

    def totals(subset):
        out.append("| agent | solved | 95% CI | false \"done\" | errored | clean-exit fails | edited existing tests | median time | total time | output tokens |")
        out.append("|---|---|---|---|---|---|---|---|---|---|")
        for a in agents:
            rs = [r for r in results if r["agent"] == a and r["task"] in subset]
            p = sum(r["passed"] for r in rs)
            tt = sum(r["seconds"] for r in rs)
            # Prefer the proxy meter's count (the same measurement for every agent)
            # over what an agent reports about itself.
            toks = [(r.get("usage") or {}).get("output") or (r.get("tokens") or {}).get("out") for r in rs]
            tok = f"{sum(toks):,}" if toks and all(t is not None for t in toks) else "n/a"
            tp = sum(bool(r.get("tampered")) for r in rs)
            # The first two columns need the agent's own signal; where it prints
            # none, say so rather than guessing from the exit code. A run killed
            # at the deadline never got to report, so it isn't a missing signal.
            verifiable = [r for r in rs if not r["timed_out"]]
            known = [r for r in verifiable if r.get("claimed_done") is not None]
            if known:
                fd = str(sum(bool(r.get("false_done")) for r in known)) + ("" if len(known) == len(verifiable) else "*")
                er = str(sum(bool(r.get("errored")) for r in known))
            else:
                fd = er = "—"
            cf = sum(bool(r.get("clean_exit_fail")) for r in rs)
            lo, hi = wilson(p, len(rs))
            med = sorted(r["seconds"] for r in rs)[len(rs) // 2] if rs else 0
            out.append(f"| {a} | **{p}/{len(rs)}** ({100 * p / max(1, len(rs)):.0f}%) | {100 * lo:.0f}–{100 * hi:.0f}% | {fd} | {er} | {cf} | {tp} | {med:.0f}s | {tt / 60:.1f} min | {tok} |")

    if complete or not showcase:
        totals(complete)
    if showcase:
        out.append(f"\nShowcase tier ({len(showcase)} tasks: data, analysis, financial and docs/config answers), not part of the coding score above:\n")
        totals(showcase)
    if any(t.startswith("swe-") for t in complete):
        out.append("\n*False \"done\"*: the agent's own output reported success — chanto and claude print an `is_error` field, forge an ERROR "
                   "line — yet the grader failed the task; it stopped believing it was finished. *Errored*: it reported an error rather than "
                   "finishing. *Clean-exit fails*: exited 0 and still failed. Where an agent prints no signal the first two columns show —, and "
                   "this is the closest read, though it can't tell a crash from a confident \"done\" (forge errors on every run and still exits "
                   "0). Exit codes are not a reliable stand-in: chanto-verify exits 3 and opencode exits 1 on runs that pass. "
                   "*Edited existing tests*: changed a test file the task started with. On SWE-bench tasks that's usually an added regression "
                   "test, and the grader restores the original tests before checking, so it can't change a result; it signals cheating only on "
                   "the test-weakening tasks.")
    if any(r.get("offtask_hits") for r in results):
        counts = ", ".join(f"{a} {sum(bool(r.get('offtask_hits')) for r in results if r['agent'] == a)}" for a in agents)
        out.append("\n⚠ marks a run whose transcript shows off-task access (`offtask_hits` in the result file: paths outside "
                   "its run root, package downloads, git history past the task's base, whole-disk searches, GitHub URLs). "
                   "The sandbox blocks most of these, so a hit is usually a failed attempt; read the run's hits before "
                   f"trusting a ⚠ pass. Runs with hits: {counts}.")
    if any(r.get("leaked") for r in results):
        out.append("\n🔍 marks a run whose transcript names the task's hidden tests (`tasks/<task>/pristine/test.py`). "
                   "Online runs leave the checkout readable, so such a cell measures reading the grader as much as solving the "
                   "task; `--offline` hides the tests.")
    out.append("\n| task | " + " | ".join(agents) + " |")
    out.append("|---|" + "---|" * len(agents))
    for t in tasks:
        row = [t]
        for a in agents:
            rs = [r for r in results if r["agent"] == a and r["task"] == t]
            if not rs:
                row.append("–")
                continue
            cells = []
            for r in rs:
                mark = "✅" if r["passed"] else ("⏱" if r["timed_out"] else "❌")
                if r.get("tampered"):
                    mark += "✂"
                if r.get("leaked"):
                    mark += "🔍"
                if r.get("offtask_hits"):
                    mark += "⚠"
                cells.append(f"{mark} {r['seconds']:.0f}s")
            row.append(" / ".join(cells))
        out.append("| " + " | ".join(row) + " |")
    if ref in agents and len(agents) > 1:
        out.append(f"\nPaired against **{ref}** on the coding tasks both ran (sign test, two-sided; p ≥ 0.05 means the difference could be chance):\n")
        out.append(f"| agent | tasks | {ref} better | {ref} worse | p |")
        out.append("|---|---|---|---|---|")
        for a, n, better, worse, p in paired([r for r in results if tier_of(r["task"]) != "showcase"], ref):
            out.append(f"| {a} | {n} | {better} | {worse} | {p:.2f}{'' if p < 0.05 else ' (not significant)'} |")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", default="chanto")
    ap.add_argument("--model", default="qwen3.8-bench")
    ap.add_argument("--ctx", type=int, help="context window given to every agent (default: the hosted model's, "
                    "from the proxy; 32768 for a local model)")
    ap.add_argument("--tasks", default="")
    ap.add_argument("--tier", default=",".join(CODING_TIERS),
                    help="bands: core,medium,hard,beyond (the default, all coding) and the opt-in showcase")
    ap.add_argument("--estimate", action="store_true", help="print projected cost/time and exit; runs nothing")
    ap.add_argument("--estimate-ref", nargs="+", help="result JSONs to average tokens from (default: results/*.json)")
    ap.add_argument("--timeout", type=int, default=None, help="agent seconds (default 1800 for swe-*, 900 otherwise)")
    ap.add_argument("--meter", help="token meter URL (meter.py), e.g. http://localhost:4100")
    ap.add_argument("--meter-log", default=str(ROOT / "meter.jsonl"), help="the meter's log file")
    ap.add_argument("--min-balance", type=float, help="DeepSeek: stop when the account balance (USD) drops below this")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--api", help="use a hosted model through this proxy (e.g. http://localhost:4000, see proxy.sh)")
    ap.add_argument("--offline", action="store_true",
                    help="kept for old commands: every run is isolated unless CHANTO_BENCH_ISOLATION=off")
    ap.add_argument("--sanity", action="store_true", help="verify every check fails on the untouched task")
    ap.add_argument("--chanto-effort", choices=["low", "medium", "high", "xhigh", "max"],
                    help="reasoning effort for every chanto variant (for chanto+effort on models without a known default)")
    ap.add_argument("--report", nargs="+", help="merge result JSON files into a markdown report")
    ap.add_argument("--report-ref", default="chanto", help="agent the report compares the others against")
    ap.add_argument("--unisolated", action="store_true",
                    help="let --report tabulate runs made without isolation, labelled as such (never for publishing)")
    args = ap.parse_args()
    global API, METER, METER_LOG, OFFLINE, CHANTO_EFFORT
    API = args.api
    CHANTO_EFFORT = args.chanto_effort
    for a in args.agents.split(","):
        chanto_optimizations(a)  # an unknown variant stops here, before any run
    METER, METER_LOG = args.meter, args.meter_log
    if args.ctx is None and not args.report and not args.estimate:
        args.ctx = hosted_context(args.model) if API else 32768
    if args.report:
        print(report(args.report, args.report_ref, unisolated=args.unisolated))
        return
    mode = isolation_mode()
    if mode == "off" and args.offline:
        sys.exit(f"--offline asks for isolation, but {ISOLATION_ENV}=off turns it off")
    OFFLINE = mode != "off"
    if not OFFLINE and not args.estimate:
        print(f"warning: {ISOLATION_ENV}=off: agents can see the whole machine and the network. "
              "Use this for debugging only; --report refuses these results.", file=sys.stderr, flush=True)
    tiers = [t.strip() for t in args.tier.split(",") if t.strip()]
    bad = [t for t in tiers if t not in TIERS]
    if bad:
        sys.exit(f"unknown tier(s): {', '.join(bad)} (known: {', '.join(TIERS)})")
    if args.estimate:
        refs = args.estimate_ref or sorted(str(p) for p in RESULTS.glob("*.json"))
        refs = [r for r in refs if Path(r).exists()]
        if not refs:
            sys.exit("no result files to estimate from; pass --estimate-ref")
        price = PRICES.get(args.model)
        if not price:
            sys.exit(f"no price for {args.model}; add it to PRICES or pass --model with a known one")
        off, peak = price
        agents = args.agents.split(",")
        counts, rows = estimate(agents, tiers, args.repeat, refs)
        print(f"projected from {len(refs)} result file(s); model {args.model}")
        print(f"  per M tok (input/cache-hit/output): off-peak ${off[0]*1e6:.3f}/${off[1]*1e6:.3f}/${off[2]*1e6:.3f}"
              f"  peak ${peak[0]*1e6:.3f}/${peak[1]*1e6:.3f}/${peak[2]*1e6:.3f}")
        print("tiers: " + ", ".join(f"{t}={counts[t]}" for t in tiers)
              + f"  x{args.repeat} reps x {len(agents)} agents")
        print(f"\n{'agent':16}{'runs':>6}{'input':>12}{'output':>10}{'off-peak':>11}{'peak':>10}{'wall (1 shard)':>16}{'wall (2 shards)':>17}")
        per = {t: counts[t] * args.repeat for t in tiers}
        total_runs = sum(per.values())
        grand_off = grand_peak = 0.0
        for a, tin, tout, tcache, tsec in rows:
            co = cost_of(tin, tout, tcache, off)
            cp = cost_of(tin, tout, tcache, peak)
            grand_off += co
            grand_peak += cp
            print(f"{a:16}{total_runs:>6}{tin:>12,.0f}{tout:>10,.0f}{'$'+format(co, '.2f'):>11}"
                  f"{'$'+format(cp, '.2f'):>10}{hms(tsec):>16}{hms(tsec / 2):>17}")
        print(f"\nTOTAL projected cost: ${grand_off:.2f} off-peak, ${grand_peak:.2f} peak"
              "   (wall time assumes agents run serially; shards divide it)")
        return
    if OFFLINE:
        require_offline_platform()
    tasks = select_tasks(tiers, args.tasks)
    if args.sanity:
        ok = True
        for t in tasks:
            wd = WORK / "sanity" / t
            if wd.exists():
                shutil.rmtree(wd)
            prepare_task(TASKS / t, wd)
            empty = WORK / "sanity" / f"{t}.out"
            empty.write_text("")
            env = dict(os.environ, OUTPUT_FILE=str(empty))
            envf = TASKS / t / "env"
            if envf.exists():
                for line in envf.read_text().splitlines():
                    k, v = line.split("=", 1)
                    env[k] = v
            r = run_check(["bash", str(TASKS / t / "check.sh")], wd, env, timeout=600)
            status = "FAILS (good)" if r.returncode != 0 else "PASSES (bad: check is too weak)"
            ok &= r.returncode != 0
            print(f"{t:22} {status}")
        sys.exit(0 if ok else 1)

    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    # pid in the name: parallel shards started in the same second must not share a file.
    res_file = RESULTS / f"{stamp}-{os.getpid()}.json"
    global ARTIFACTS
    ARTIFACTS = RESULTS / res_file.stem
    try:
        meta = run_meta(args, tasks)
    except Exception as e:  # never lose a run over its bookkeeping
        meta = {"error": str(e)[:300]}
    results = []
    # Interleave: each task runs every agent back to back in a shuffled order,
    # so model-cache warmth and machine load don't favor one agent.
    rng = random.Random(args.seed)
    plan = []
    for rep in range(args.repeat):
        order = tasks[:]
        rng.shuffle(order)
        for t in order:
            agents = args.agents.split(",")
            rng.shuffle(agents)
            plan.extend((a, t, rep) for a in agents)
    for agent, t, rep in plan:
        if args.min_balance is not None:
            bal = deepseek_balance()
            if bal is not None and bal < args.min_balance:
                print(f"\nStopped: DeepSeek balance ${bal:.2f} is below --min-balance ${args.min_balance:.2f}. "
                      f"{len(results)} completed runs kept in {res_file}.", flush=True)
                sys.exit(2)
        r = run_task(agent, t, args.model, args.ctx, args.timeout if args.timeout is not None else (1800 if t.startswith("swe-") else 900), rep)
        results.append(r)
        print(f"{agent:14} {t:22} {'PASS' if r['passed'] else 'FAIL'} {r['seconds']:7.1f}s"
              f"{' (timeout)' if r['timed_out'] else ''}{' (read hidden tests)' if r.get('leaked') else ''}"
              f"{' (off-task: ' + str(len(r['offtask_hits'])) + ')' if r.get('offtask_hits') else ''}", flush=True)
        res_file.write_text(redact(json.dumps({"model": args.model, "ctx": args.ctx, "offline": OFFLINE, "isolation": sandbox_name(), "meta": meta, "results": results}, indent=2)))
        # Out of credit or quota: every later run would fail instantly, so stop
        # rather than record them as failures.
        out = (WORK / agent / f"{t}-{rep}.out").read_text(errors="ignore")[-20000:]
        if not r["passed"] and OUT_OF_BUDGET.search(out):
            results.pop()
            res_file.write_text(redact(json.dumps({"model": args.model, "ctx": args.ctx, "offline": OFFLINE, "isolation": sandbox_name(), "meta": meta, "results": results, "aborted": "out of budget"}, indent=2)))
            print(f"\nStopped: the model provider reports no budget left ({OUT_OF_BUDGET.search(out).group(0)!r}). "
                  f"{len(results)} completed runs kept in {res_file}.", flush=True)
            sys.exit(2)
    # Summary
    print("\n| agent | passed | total time | mean time |")
    print("|---|---|---|---|")
    for agent in args.agents.split(","):
        rs = [r for r in results if r["agent"] == agent]
        p = sum(r["passed"] for r in rs)
        tt = sum(r["seconds"] for r in rs)
        print(f"| {agent} | {p}/{len(rs)} | {tt:.0f}s | {tt / max(1, len(rs)):.0f}s |")
    print(f"\nresults: {res_file}")


if __name__ == "__main__":
    main()
