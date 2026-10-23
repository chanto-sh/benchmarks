# Extra benchmarks

Things the task-solving table in `RESULTS.md` does not measure. Each
script prints markdown and has no dependencies beyond Python 3 and a debug
build (`cargo build`).

| script | what it measures | needs a model |
|---|---|---|
| `efficiency.py` | tool-loop cost: calls, tokens, cache hits, time, false "done" per agent; paired head-to-head vs a baseline | no |
| `cli_overhead.py` | binary size, startup/`--help` latency, peak RSS vs other installed CLIs | no |
| `safety_eval.py` | fast-path allow/defer for routine vs dangerous commands, then the model classifier | part 2 |
| `protocol.py` | MCP (`mcp-serve`), ACP, `--output-format json`/`stream-json`, `--input-format stream-json`, exit codes | yes |
| `resume.py` | SIGINT during a Bash call: prompt exit, no orphaned child, session still resumable | yes |

Model-backed scripts read the same proxy settings as `run.py`, either
from flags or the environment:

```sh
export BENCH_PROVIDER=openai
export BENCH_BASE_URL=http://localhost:4000/v1
export BENCH_MODEL=bench-model
export BENCH_API_KEY=sk-bench-local
```

## Results

The consolidated results are in `RESULTS.md`. Raw output per benchmark:
`efficiency.md`, `cli_overhead.md`, `safety.md`, `protocol.md`, `resume.md`.

`efficiency.py` is meant to run on a finished `results/*.json` set; pass
just the files for one run so unrelated runs do not mix.

```sh
python3 extra/efficiency.py results/20261018-150904-*.json \
    results/20261018-1721*.json
```

`cli_overhead.py` uses an empty `CHANTO_HOME` so a user's plugins and MCP
servers do not count as startup cost.

## Not measured here

- **Retrieval quality**: `SemanticSearch` needs an embedding endpoint, and this
  machine's Ollama has no models; `RepoMap` is an orientation aid rather than a
  query-driven search, so a hit-rate comparison against `rg` would not be fair.
- **Parallel fan-out**: a credible measurement needs an idle machine and a
  model that reliably issues independent tool calls; run `chanto team` against
  the same sub-tasks serially once the main benchmark is not saturating the
  proxy.
