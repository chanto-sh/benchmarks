708 cells over 40 tasks

| agent | solved | 95% CI | false "done" | timeouts | median calls | median calls (solved) | median in tok | median out tok | cache hit | median time |
|---|---|---|---|---|---|---|---|---|---|---|
| cline | 98/118 (83%) | 75–89% | n/a | 0 | 14 | 14 | 244,616 | 11,616 | 97% | 89s |
| opencode | 97/118 (82%) | 74–88% | n/a | 0 | 15 | 15 | 291,348 | 9,680 | 96% | 105s |
| claude | 95/118 (81%) | 72–87% | 16 of 118 | 0 | 12 | 12 | 308,449 | 7,744 | 95% | 68s |
| forge | 94/118 (80%) | 72–86% | 13 of 117 | 1 | 16 | 16 | 378,916 | 10,124 | 97% | 99s |
| chanto-verify | 92/118 (78%) | 70–84% | 19 of 118 | 0 | 12 | 11 | 167,752 | 9,532 | 95% | 73s |
| Chanto | 89/118 (75%) | 67–82% | 22 of 118 | 0 | 10 | 10 | 174,456 | 8,158 | 95% | 62s |

`n/a`: `cline`, `opencode` print no structured completion signal, so a false "done" is unmeasurable (shown as zero before).

## Paired head-to-head against `chanto` (same task and rep)

| agent | pairs | only baseline | only agent | both | neither | p (sign test) |
|---|---|---|---|---|---|---|
| claude | 118 | 9 | 15 | 80 | 14 | 0.31 |
| cline | 118 | 6 | 15 | 83 | 14 | 0.08 |
| forge | 118 | 9 | 14 | 80 | 15 | 0.40 |
| chanto-verify | 118 | 8 | 11 | 81 | 18 | 0.65 |
| opencode | 118 | 7 | 15 | 82 | 14 | 0.13 |
