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

`*` that CLI has no `--version`; `--help` is used for startup.
`launcher` means the executable is a small wrapper around a JS bundle, so its own size is not the runtime's.

Startup is `--version` (or `--help` where marked `*`) p50 over 7 runs, first discarded. Chanto runs with an empty `CHANTO_HOME`, so a user's plugins and MCP servers don't skew it.

Chanto paths that never call a model:

| path | p50 |
|---|---|
| `--run-tool Read` | 84 ms |
| `--dump-prompt` | 84 ms |

Timings are warm-cache wall clock; the machine also ran the task benchmark, so treat differences under ~20 ms as noise.
