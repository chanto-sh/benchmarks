| check | result | detail |
|---|---|---|
| mcp: initialize | pass | 2024-11-05 |
| mcp: tools/list | pass | 2 tools |
| mcp: tools/call | pass | Chanto |
| acp: initialize | pass | protocolVersion 1 |
| acp: unknown session errors | pass | unknown session |
| acp: still alive | pass | exit None |
| cli: bad flag is a usage error | pass | exit 2 |
| cli: --help exits 0 | pass | exit 0 |
| json: one object | pass | result |
| json: documented fields | pass | all present |
| json: no error | pass | exit 0 |
| stream: every line is JSON | pass | 3 events |
| stream: ends in result | pass | result |
| stream: result has fields | pass | all present |
| stream-in: one turn per line | pass | 3 events |
| stream-in: result | pass | result |

16/16 checks pass
