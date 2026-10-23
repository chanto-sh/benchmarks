942 cells over 157 tasks

| agent | solved | 95% CI | false "done" | timeouts | median calls | median calls (solved) | median in tok | median out tok | cache hit | median time |
|---|---|---|---|---|---|---|---|---|---|---|
| cline | 152/157 (97%) | 93–99% | n/a | 0 | n/a | n/a | n/a | n/a | n/a | 15s |
| claude | 149/157 (95%) | 90–97% | 8 of 157 | 0 | n/a | n/a | 18,659 | 1,586 | 0% | 14s |
| chanto | 148/157 (94%) | 89–97% | 9 of 157 | 0 | n/a | n/a | 36,396 | 1,221 | 0% | 12s |
| forge | 148/157 (94%) | 89–97% | 9 of 157 | 0 | n/a | n/a | n/a | n/a | n/a | 17s |
| codex | 148/157 (94%) | 89–97% | n/a | 0 | n/a | n/a | n/a | n/a | n/a | 17s |
| opencode | 145/157 (92%) | 87–96% | n/a | 0 | n/a | n/a | n/a | n/a | n/a | 13s |

`n/a`: `cline`, `codex`, `opencode` print no structured completion signal, so a false "done" is unmeasurable (shown as zero before).

## Paired head-to-head against `chanto` (same task and rep)

| agent | pairs | only baseline | only agent | both | neither | p (sign test) |
|---|---|---|---|---|---|---|
| claude | 157 | 2 | 3 | 146 | 6 | 1.00 |
| cline | 157 | 1 | 5 | 147 | 4 | 0.22 |
| codex | 157 | 2 | 2 | 146 | 7 | 1.00 |
| forge | 157 | 4 | 4 | 144 | 5 | 1.00 |
| opencode | 157 | 4 | 1 | 144 | 8 | 0.38 |
