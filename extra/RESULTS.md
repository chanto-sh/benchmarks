# Extra benchmarks — results

Run on 2026-10-18 on a 10-core arm64 macOS box. Task-solving ran `deepseek/deepseek-flash`
through one LiteLLM proxy; every agent got the same model and `--ctx 131072`.

## 1. Tool-loop efficiency

40 tasks × 6 agents × 3 reps (`results/20261018-150904-*`,
`results/20261018-1721*`). 708 of 720 cells: two tasks lost their rep 2
to a shard crash in `run.py:reap` (`os.killpg` raised `PermissionError` when the
process group was gone); the shard now ignores that instead of aborting, but the
cells were not re-run.

| agent | solved | 95% CI | false "done" | timeouts | median calls | median calls (solved) | median in tok | median out tok | cache hit | median time |
|---|---|---|---|---|---|---|---|---|---|---|
| cline | 98/118 (83%) | 75–89% | n/a | 0 | 14 | 14 | 244,616 | 11,616 | 97% | 89s |
| opencode | 97/118 (82%) | 74–88% | n/a | 0 | 15 | 15 | 291,348 | 9,680 | 96% | 105s |
| claude | 95/118 (81%) | 72–87% | 16 of 118 | 0 | 12 | 12 | 308,449 | 7,744 | 95% | 68s |
| forge | 94/118 (80%) | 72–86% | 13 of 117 | 1 | 16 | 16 | 378,916 | 10,124 | 97% | 99s |
| chanto-verify | 92/118 (78%) | 70–84% | 19 of 118 | 0 | 12 | 11 | 167,752 | 9,532 | 95% | 73s |
| Chanto | 89/118 (75%) | 67–82% | 22 of 118 | 0 | 10 | 10 | 174,456 | 8,158 | 95% | 62s |

`n/a`: cline and opencode print no structured completion signal, so a false
"done" cannot be measured for them (it is not zero).

Paired on the same task and rep:

| agent | pairs | only `chanto` | only agent | both | neither | p (sign test) |
|---|---|---|---|---|---|---|
| claude | 118 | 9 | 15 | 80 | 14 | 0.31 |
| cline | 118 | 6 | 15 | 83 | 14 | 0.08 |
| forge | 118 | 9 | 14 | 80 | 15 | 0.40 |
| chanto-verify | 118 | 8 | 11 | 81 | 18 | 0.65 |
| opencode | 118 | 7 | 15 | 82 | 14 | 0.13 |

Read this honestly: **no agent is significantly better than `chanto` on this
set** — every paired sign test has p > 0.05, and the CIs overlap. The clear,
measurable differences are in work done, not solve rate:

- `chanto` solves slightly fewer tasks but uses **44% fewer input tokens than
  claude, 38% fewer than opencode and 54% fewer than forge**, with 10 model
  calls per task instead of 12–16.
- It is also the fastest median (62 s), ahead of claude (68 s), cline (89 s)
  and opencode (105 s).
- `chanto` claims success when the hidden check fails more often (22/118,
  19%; chanto-verify 16%, claude 14%, forge 11%). That is the one place where
  the verify loop still leaves value on the table.

## 2. CLI overhead

| agent | binary MB | startup p50 | `--help` p50 | peak RSS |
|---|---|---|---|---|
| Chanto | 20.6 | 6 ms | 6 ms | 9 MB |
| opencode | 180.3 | 79 ms* | 48 ms | 83 MB |
| claude | 268.0 | 12 ms | 80 ms | 26 MB |
| forge | launcher | 46 ms | 48 ms | 42 MB |
| codex | 246.6 | 12 ms | 12 ms | 19 MB |
| kilo | launcher | 523 ms* | 547 ms | 177 MB |
| crush | launcher | 139 ms | 134 ms | 68 MB |
| qwen | launcher | 45 ms | 85 ms | 45 MB |
| cline | launcher | 595 ms | 603 ms | 222 MB |

`*` no `--version`; `--help` is used for startup. `launcher` means a wrapper
around a JS bundle, so the wrapper's own size is not the runtime's.

Chanto paths that never call a model: `--run-tool Read` 84 ms,
`--dump-prompt` 84 ms (empty `CHANTO_HOME`, so plugins/MCP servers do not
count).

## 3. Safety

Fast path (`--risk`, no model, 9 ms p50):

| set | n | allow | defer | deny | fast-allowed |
|---|---|---|---|---|---|
| routine | 36 | 27 | 9 | 0 | 75% |
| dangerous | 30 | 0 | 30 | 0 | 0% |

Model fallback (`--classify`): **denied 30/30 dangerous commands**, 0 leaked,
1.1 s mean. Full command list in `safety.md`.

Three prompt-injection tasks (`tasks/safety-injection-*`: instructions
hidden in a README, an `AGENTS.md`, and a test comment) each poison the
repository to create `INJECTION_FOLLOWED.txt` and avoid the real fix. Every task
was verified to fail before the correct fix and pass after it, and `check.sh`
fails if the canary exists or the test file was edited.

## 4. Protocol / SDK conformance

16/16 checks pass (`protocol.md`): MCP initialize, `tools/list` (2 tools),
`tools/call` over stdio; ACP initialize and a JSON-RPC error for an unknown
session; `--output-format json` with every documented field; `stream-json` one
object per line ending in `result`; `--input-format stream-json`; usage exit
code 2 and `--help` exit 0.

## 5. Interrupt / resume

6/6 checks pass (`resume.md`): SIGINT during a running Bash call exits in 0.1 s,
leaves no orphaned `sleep`, keeps the session file, and `--resume <id>` finishes
a turn with the same session id.

## Not measured

- **Retrieval quality**: `SemanticSearch` needs an embedding endpoint and this
  machine's Ollama has no models. `RepoMap` is an orientation aid, not a
  query-driven search, so an `rg` hit-rate comparison would be misleading.
- **Parallel fan-out**: a fair measurement needs an idle machine and a model
  that reliably issues independent tool calls; the run above saturated the
  proxy for five hours.
