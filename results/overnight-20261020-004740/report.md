Model: `deepseek/deepseek-flash` (as `bench-model`) through one proxy for all agents · context 32768

| agent | solved | 95% CI | false "done" | errored | clean-exit fails | edited existing tests | median time | total time | output tokens |
|---|---|---|---|---|---|---|---|---|---|
| forge | **148/157** (94%) | 89–97% | 9 | 0 | 9 | 0 | 17s | 58.7 min | n/a |
| codex | **148/157** (94%) | 89–97% | — | — | 9 | 0 | 17s | 59.2 min | n/a |
| claude | **149/157** (95%) | 90–97% | 8 | 0 | 8 | 0 | 14s | 53.2 min | 416,358 |
| cline | **152/157** (97%) | 93–99% | — | — | 5 | 0 | 15s | 58.9 min | n/a |
| opencode | **145/157** (92%) | 87–96% | — | — | 9 | 0 | 13s | 46.7 min | n/a |
| chanto | **148/157** (94%) | 89–97% | 9 | 0 | 9 | 0 | 12s | 53.8 min | 338,937 |

| task | forge | codex | claude | cline | opencode | chanto |
|---|---|---|---|---|---|---|
| humaneval-0 | ✅ 10s | ✅ 11s | ✅ 8s | ✅ 7s | ✅ 10s | ✅ 10s |
| humaneval-10 | ✅ 14s | ✅ 11s | ✅ 11s | ✅ 14s | ✅ 14s | ✅ 9s |
| humaneval-108 | ✅ 13s | ✅ 14s | ✅ 12s | ✅ 12s | ✅ 20s | ✅ 9s |
| humaneval-113 | ✅ 8s | ✅ 12s | ✅ 14s | ✅ 11s | ✅ 18s | ✅ 14s |
| humaneval-114 | ✅ 9s | ✅ 10s | ✅ 10s | ✅ 8s | ✅ 7s | ✅ 9s |
| humaneval-115 | ✅ 14s | ✅ 7s | ✅ 11s | ✅ 12s | ✅ 8s | ✅ 8s |
| humaneval-125 | ❌ 31s | ✅ 13s | ✅ 16s | ✅ 18s | ❌ 76s | ✅ 12s |
| humaneval-132 | ❌ 29s | ❌ 18s | ❌ 17s | ❌ 19s | ❌ 44s | ❌ 33s |
| humaneval-136 | ✅ 9s | ✅ 12s | ✅ 14s | ✅ 10s | ✅ 7s | ✅ 10s |
| humaneval-145 | ✅ 31s | ✅ 40s | ✅ 73s | ✅ 119s | ✅ 12s | ✅ 32s |
| humaneval-153 | ✅ 11s | ✅ 10s | ✅ 15s | ✅ 20s | ✅ 9s | ✅ 13s |
| humaneval-158 | ✅ 8s | ✅ 10s | ✅ 13s | ✅ 8s | ✅ 9s | ✅ 11s |
| humaneval-159 | ✅ 7s | ✅ 5s | ✅ 9s | ✅ 10s | ✅ 8s | ✅ 9s |
| humaneval-163 | ✅ 18s | ✅ 17s | ✅ 33s | ❌ 15s | ✅ 24s | ✅ 12s |
| humaneval-2 | ✅ 11s | ✅ 12s | ✅ 9s | ✅ 9s | ✅ 7s | ✅ 10s |
| humaneval-30 | ✅ 8s | ✅ 12s | ✅ 11s | ✅ 9s | ✅ 8s | ✅ 8s |
| humaneval-37 | ✅ 8s | ✅ 9s | ✅ 9s | ✅ 9s | ✅ 7s | ✅ 11s |
| humaneval-45 | ✅ 6s | ✅ 7s | ✅ 8s | ✅ 9s | ✅ 7s | ✅ 8s |
| humaneval-46 | ✅ 13s | ✅ 11s | ✅ 12s | ✅ 12s | ✅ 8s | ✅ 10s |
| humaneval-5 | ✅ 10s | ✅ 12s | ✅ 12s | ✅ 10s | ✅ 10s | ✅ 12s |
| humaneval-60 | ✅ 8s | ✅ 6s | ✅ 8s | ✅ 16s | ✅ 9s | ✅ 7s |
| humaneval-62 | ✅ 8s | ✅ 6s | ✅ 8s | ✅ 7s | ✅ 8s | ✅ 9s |
| humaneval-63 | ✅ 10s | ✅ 9s | ✅ 10s | ✅ 7s | ✅ 9s | ✅ 9s |
| humaneval-66 | ✅ 7s | ✅ 10s | ✅ 10s | ✅ 10s | ✅ 9s | ✅ 10s |
| humaneval-69 | ✅ 10s | ✅ 11s | ✅ 12s | ✅ 10s | ✅ 7s | ✅ 9s |
| humaneval-70 | ✅ 8s | ✅ 15s | ✅ 8s | ✅ 10s | ✅ 8s | ✅ 7s |
| humaneval-75 | ✅ 11s | ✅ 20s | ✅ 10s | ✅ 15s | ✅ 19s | ✅ 25s |
| humaneval-82 | ✅ 8s | ✅ 14s | ✅ 5s | ✅ 8s | ✅ 8s | ✅ 12s |
| humaneval-90 | ✅ 8s | ✅ 12s | ✅ 10s | ✅ 8s | ✅ 9s | ✅ 14s |
| humaneval-95 | ✅ 15s | ✅ 8s | ✅ 14s | ✅ 10s | ✅ 10s | ✅ 10s |
| mbpp-226 | ✅ 7s | ✅ 6s | ✅ 9s | ✅ 9s | ✅ 5s | ✅ 8s |
| mbpp-244 | ✅ 12s | ❌ 10s | ❌ 12s | ✅ 17s | ❌ 9s | ❌ 10s |
| mbpp-265 | ❌ 29s | ✅ 27s | ❌ 12s | ❌ 10s | ❌ 11s | ❌ 19s |
| mbpp-274 | ✅ 9s | ✅ 8s | ✅ 13s | ✅ 8s | ✅ 9s | ✅ 8s |
| mbpp-283 | ✅ 9s | ✅ 12s | ✅ 12s | ✅ 16s | ❌ 19s | ✅ 13s |
| mbpp-297 | ✅ 10s | ✅ 10s | ✅ 13s | ✅ 10s | ✅ 9s | ✅ 12s |
| mbpp-311 | ❌ 16s | ✅ 18s | ❌ 16s | ❌ 29s | ❌ 11s | ❌ 17s |
| mbpp-410 | ❌ 27s | ✅ 14s | ✅ 24s | ✅ 70s | ✅ 47s | ✅ 16s |
| mbpp-433 | ✅ 6s | ✅ 7s | ✅ 11s | ✅ 15s | ✅ 9s | ✅ 10s |
| mbpp-441 | ✅ 9s | ✅ 8s | ✅ 9s | ✅ 9s | ✅ 9s | ✅ 10s |
| mbpp-445 | ✅ 9s | ❌ 7s | ✅ 13s | ✅ 13s | ❌ 12s | ❌ 11s |
| mbpp-446 | ✅ 9s | ❌ 14s | ❌ 13s | ✅ 8s | ✅ 15s | ❌ 27s |
| mbpp-463 | ✅ 11s | ✅ 9s | ✅ 11s | ✅ 9s | ✅ 10s | ✅ 143s |
| mbpp-465 | ❌ 12s | ✅ 24s | ✅ 12s | ✅ 32s | ✅ 63s | ✅ 21s |
| mbpp-558 | ✅ 12s | ❌ 21s | ✅ 12s | ✅ 13s | ❌ 14s | ✅ 12s |
| mbpp-567 | ✅ 8s | ✅ 8s | ✅ 12s | ✅ 9s | ✅ 10s | ✅ 11s |
| mbpp-597 | ✅ 26s | ❌ 23s | ✅ 54s | ✅ 60s | ❌ 23s | ❌ 14s |
| mbpp-615 | ✅ 13s | ❌ 8s | ❌ 12s | ✅ 75s | ❌ 9s | ✅ 12s |
| mbpp-62 | ✅ 9s | ✅ 7s | ✅ 10s | ✅ 10s | ✅ 10s | ✅ 10s |
| mbpp-63 | ✅ 11s | ✅ 16s | ✅ 13s | ✅ 11s | ✅ 67s | ✅ 146s |
| mbpp-630 | ❌ 14s | ✅ 26s | ❌ 12s | ✅ 16s | ✅ 14s | ✅ 25s |
| mbpp-71 | ✅ 9s | ✅ 9s | ✅ 12s | ✅ 12s | ✅ 10s | ✅ 14s |
| mbpp-745 | ✅ 10s | ✅ 13s | ✅ 12s | ✅ 50s | ✅ 9s | ✅ 12s |
| mbpp-751 | ❌ 13s | ❌ 11s | ❌ 18s | ❌ 18s | ❌ 8s | ❌ 12s |
| mbpp-752 | ✅ 8s | ✅ 8s | ✅ 8s | ✅ 11s | ✅ 8s | ✅ 7s |
| mbpp-765 | ❌ 12s | ❌ 10s | ✅ 23s | ✅ 51s | ❌ 9s | ❌ 12s |
| mbpp-782 | ✅ 8s | ✅ 8s | ✅ 12s | ✅ 10s | ✅ 9s | ✅ 12s |
| mbpp-88 | ✅ 8s | ✅ 10s | ✅ 10s | ✅ 9s | ✅ 7s | ✅ 9s |
| mbpp-9 | ✅ 10s | ✅ 12s | ✅ 11s | ✅ 14s | ✅ 9s | ✅ 11s |
| mbpp-98 | ✅ 9s | ✅ 16s | ✅ 8s | ✅ 17s | ✅ 23s | ✅ 8s |
| poly-go-alphametics | ✅ 67s | ✅ 59s | ✅ 59s | ✅ 51s | ✅ 35s | ✅ 80s |
| poly-go-beer-song | ✅ 22s | ✅ 15s | ✅ 16s | ✅ 26s | ✅ 17s | ✅ 12s |
| poly-go-book-store | ✅ 29s | ✅ 24s | ✅ 22s | ✅ 93s | ✅ 20s | ✅ 24s |
| poly-go-bottle-song | ✅ 19s | ✅ 18s | ✅ 11s | ✅ 14s | ✅ 13s | ✅ 10s |
| poly-go-bowling | ✅ 38s | ✅ 30s | ✅ 20s | ✅ 46s | ✅ 26s | ✅ 53s |
| poly-go-connect | ✅ 50s | ✅ 41s | ✅ 34s | ✅ 41s | ✅ 15s | ✅ 16s |
| poly-go-crypto-square | ✅ 18s | ✅ 14s | ✅ 12s | ✅ 13s | ✅ 19s | ✅ 14s |
| poly-go-dnd-character | ✅ 24s | ✅ 18s | ✅ 18s | ✅ 16s | ✅ 14s | ✅ 13s |
| poly-go-dominoes | ✅ 22s | ✅ 63s | ✅ 25s | ✅ 15s | ✅ 19s | ✅ 10s |
| poly-go-error-handling | ✅ 20s | ✅ 21s | ✅ 12s | ✅ 14s | ✅ 13s | ✅ 13s |
| poly-go-food-chain | ✅ 20s | ✅ 15s | ✅ 14s | ✅ 22s | ✅ 11s | ✅ 14s |
| poly-go-forth | ✅ 40s | ✅ 38s | ✅ 34s | ✅ 33s | ✅ 34s | ✅ 26s |
| poly-go-hexadecimal | ✅ 21s | ✅ 17s | ✅ 16s | ✅ 17s | ✅ 14s | ✅ 12s |
| poly-go-kindergarten-garden | ✅ 29s | ✅ 19s | ✅ 16s | ✅ 22s | ✅ 28s | ✅ 14s |
| poly-go-matrix | ✅ 20s | ✅ 17s | ✅ 10s | ✅ 19s | ✅ 13s | ✅ 10s |
| poly-go-octal | ✅ 17s | ✅ 15s | ✅ 10s | ✅ 13s | ✅ 10s | ✅ 9s |
| poly-go-paasio | ✅ 21s | ✅ 27s | ✅ 23s | ✅ 19s | ✅ 19s | ✅ 15s |
| poly-go-palindrome-products | ✅ 21s | ✅ 28s | ✅ 17s | ✅ 14s | ✅ 22s | ✅ 32s |
| poly-go-pig-latin | ✅ 22s | ✅ 24s | ✅ 17s | ✅ 21s | ✅ 20s | ✅ 12s |
| poly-go-poker | ✅ 33s | ✅ 32s | ✅ 42s | ✅ 36s | ✅ 21s | ✅ 25s |
| poly-go-pov | ✅ 39s | ✅ 33s | ✅ 29s | ✅ 28s | ✅ 25s | ✅ 35s |
| poly-go-protein-translation | ✅ 17s | ✅ 19s | ✅ 12s | ✅ 12s | ✅ 15s | ✅ 12s |
| poly-go-react | ✅ 28s | ✅ 52s | ✅ 36s | ✅ 24s | ✅ 39s | ✅ 36s |
| poly-go-robot-simulator | ✅ 122s | ✅ 108s | ✅ 92s | ✅ 77s | ✅ 70s | ✅ 81s |
| poly-go-say | ✅ 16s | ✅ 12s | ✅ 14s | ✅ 20s | ✅ 14s | ✅ 12s |
| poly-go-scale-generator | ✅ 39s | ✅ 30s | ✅ 34s | ✅ 45s | ✅ 23s | ✅ 17s |
| poly-go-simple-linked-list | ✅ 18s | ✅ 19s | ✅ 19s | ✅ 13s | ✅ 10s | ✅ 14s |
| poly-go-sublist | ✅ 17s | ✅ 19s | ✅ 14s | ✅ 11s | ✅ 11s | ✅ 11s |
| poly-go-transpose | ✅ 25s | ✅ 19s | ✅ 16s | ✅ 30s | ✅ 16s | ✅ 10s |
| poly-go-tree-building | ✅ 24s | ✅ 24s | ✅ 21s | ✅ 18s | ✅ 19s | ✅ 20s |
| poly-go-trinary | ✅ 21s | ✅ 10s | ✅ 12s | ✅ 15s | ✅ 17s | ✅ 10s |
| poly-go-two-bucket | ✅ 32s | ✅ 40s | ✅ 21s | ✅ 28s | ✅ 35s | ✅ 40s |
| poly-go-variable-length-quantity | ✅ 13s | ✅ 36s | ✅ 14s | ✅ 10s | ✅ 29s | ✅ 23s |
| poly-go-word-search | ✅ 18s | ✅ 16s | ✅ 24s | ✅ 16s | ✅ 13s | ✅ 11s |
| poly-go-wordy | ✅ 18s | ✅ 22s | ✅ 13s | ✅ 27s | ✅ 15s | ✅ 11s |
| poly-go-zebra-puzzle | ✅ 55s | ✅ 46s | ✅ 26s | ✅ 50s | ✅ 63s | ✅ 51s |
| poly-python-affine-cipher | ✅ 8s | ✅ 16s | ✅ 9s | ✅ 13s | ✅ 8s | ✅ 8s |
| poly-python-beer-song | ✅ 8s | ✅ 16s | ✅ 8s | ✅ 9s | ✅ 10s | ✅ 9s |
| poly-python-book-store | ✅ 12s | ✅ 13s | ✅ 13s | ✅ 17s | ✅ 9s | ✅ 14s |
| poly-python-bottle-song | ✅ 14s | ✅ 13s | ✅ 15s | ✅ 12s | ✅ 11s | ✅ 7s |
| poly-python-bowling | ✅ 57s | ✅ 25s | ✅ 34s | ✅ 55s | ✅ 28s | ✅ 20s |
| poly-python-connect | ✅ 16s | ✅ 31s | ✅ 35s | ✅ 17s | ✅ 11s | ✅ 21s |
| poly-python-dominoes | ✅ 41s | ✅ 20s | ✅ 91s | ✅ 40s | ✅ 11s | ✅ 40s |
| poly-python-dot-dsl | ✅ 10s | ✅ 9s | ✅ 11s | ✅ 13s | ✅ 11s | ✅ 13s |
| poly-python-food-chain | ✅ 17s | ✅ 15s | ✅ 15s | ✅ 12s | ✅ 9s | ✅ 9s |
| poly-python-forth | ✅ 29s | ✅ 54s | ✅ 41s | ✅ 27s | ✅ 31s | ✅ 29s |
| poly-python-go-counting | ✅ 16s | ✅ 15s | ✅ 14s | ✅ 27s | ✅ 10s | ✅ 12s |
| poly-python-grade-school | ✅ 11s | ✅ 9s | ✅ 8s | ✅ 10s | ✅ 9s | ✅ 10s |
| poly-python-grep | ✅ 14s | ✅ 18s | ✅ 13s | ✅ 19s | ✅ 9s | ✅ 13s |
| poly-python-hangman | ✅ 15s | ✅ 13s | ✅ 12s | ✅ 12s | ✅ 11s | ✅ 25s |
| poly-python-list-ops | ✅ 11s | ✅ 16s | ✅ 10s | ✅ 15s | ✅ 11s | ✅ 8s |
| poly-python-paasio | ✅ 45s | ✅ 32s | ✅ 49s | ✅ 30s | ✅ 37s | ✅ 43s |
| poly-python-phone-number | ✅ 14s | ✅ 16s | ✅ 11s | ✅ 10s | ✅ 9s | ✅ 12s |
| poly-python-pig-latin | ✅ 13s | ✅ 14s | ✅ 18s | ✅ 12s | ✅ 11s | ✅ 14s |
| poly-python-poker | ✅ 14s | ✅ 16s | ✅ 13s | ✅ 22s | ✅ 14s | ✅ 11s |
| poly-python-pov | ✅ 29s | ✅ 31s | ✅ 23s | ✅ 27s | ✅ 10s | ✅ 39s |
| poly-python-proverb | ✅ 7s | ✅ 10s | ✅ 8s | ✅ 11s | ✅ 7s | ✅ 12s |
| poly-python-react | ✅ 33s | ✅ 46s | ✅ 16s | ✅ 29s | ✅ 27s | ✅ 16s |
| poly-python-rest-api | ✅ 30s | ✅ 30s | ✅ 14s | ✅ 35s | ✅ 12s | ✅ 14s |
| poly-python-robot-name | ✅ 17s | ✅ 28s | ✅ 11s | ✅ 12s | ✅ 24s | ✅ 14s |
| poly-python-scale-generator | ✅ 27s | ✅ 30s | ✅ 20s | ✅ 24s | ✅ 15s | ✅ 22s |
| poly-python-sgf-parsing | ✅ 27s | ✅ 28s | ✅ 23s | ✅ 22s | ✅ 16s | ✅ 248s |
| poly-python-simple-linked-list | ✅ 12s | ✅ 12s | ✅ 9s | ✅ 15s | ✅ 14s | ✅ 12s |
| poly-python-transpose | ✅ 19s | ✅ 29s | ✅ 20s | ✅ 24s | ✅ 45s | ✅ 16s |
| poly-python-tree-building | ✅ 15s | ✅ 18s | ✅ 12s | ✅ 18s | ✅ 12s | ✅ 10s |
| poly-python-two-bucket | ✅ 24s | ✅ 30s | ✅ 24s | ✅ 18s | ✅ 13s | ✅ 19s |
| poly-python-variable-length-quantity | ✅ 11s | ✅ 9s | ✅ 9s | ✅ 11s | ✅ 7s | ✅ 10s |
| poly-python-wordy | ✅ 15s | ✅ 27s | ✅ 15s | ✅ 15s | ✅ 14s | ✅ 14s |
| poly-python-zebra-puzzle | ✅ 32s | ✅ 27s | ✅ 18s | ✅ 93s | ✅ 27s | ✅ 12s |
| poly-python-zipper | ✅ 15s | ✅ 22s | ✅ 18s | ✅ 16s | ✅ 12s | ✅ 10s |
| poly-rust-accumulate | ✅ 18s | ✅ 10s | ✅ 14s | ✅ 9s | ✅ 11s | ✅ 9s |
| poly-rust-acronym | ✅ 28s | ✅ 22s | ✅ 16s | ✅ 18s | ✅ 12s | ✅ 24s |
| poly-rust-book-store | ✅ 38s | ✅ 33s | ✅ 189s | ✅ 17s | ✅ 14s | ✅ 11s |
| poly-rust-bowling | ✅ 49s | ✅ 35s | ✅ 37s | ✅ 37s | ✅ 20s | ✅ 29s |
| poly-rust-dot-dsl | ✅ 25s | ✅ 21s | ✅ 12s | ✅ 16s | ✅ 15s | ✅ 12s |
| poly-rust-doubly-linked-list | ✅ 94s | ✅ 55s | ✅ 81s | ✅ 68s | ✅ 69s | ✅ 56s |
| poly-rust-fizzy | ✅ 32s | ✅ 20s | ✅ 42s | ✅ 24s | ✅ 24s | ✅ 32s |
| poly-rust-forth | ✅ 54s | ✅ 51s | ✅ 37s | ✅ 38s | ✅ 34s | ✅ 33s |
| poly-rust-gigasecond | ✅ 17s | ✅ 11s | ✅ 10s | ✅ 11s | ✅ 10s | ✅ 8s |
| poly-rust-grade-school | ✅ 20s | ✅ 16s | ✅ 11s | ✅ 12s | ✅ 11s | ✅ 8s |
| poly-rust-luhn-from | ✅ 35s | ✅ 19s | ✅ 14s | ✅ 14s | ✅ 18s | ✅ 12s |
| poly-rust-macros | ✅ 32s | ✅ 18s | ✅ 18s | ✅ 16s | ✅ 14s | ✅ 12s |
| poly-rust-nucleotide-codons | ✅ 78s | ✅ 150s | ✅ 21s | ✅ 62s | ✅ 50s | ✅ 25s |
| poly-rust-ocr-numbers | ✅ 21s | ✅ 26s | ✅ 21s | ✅ 15s | ✅ 18s | ✅ 18s |
| poly-rust-parallel-letter-frequency | ✅ 40s | ✅ 26s | ✅ 18s | ✅ 24s | ✅ 28s | ✅ 12s |
| poly-rust-react | ✅ 71s | ✅ 88s | ✅ 73s | ✅ 66s | ✅ 70s | ✅ 67s |
| poly-rust-say | ✅ 22s | ✅ 12s | ✅ 10s | ✅ 12s | ✅ 10s | ✅ 10s |
| poly-rust-scale-generator | ✅ 49s | ✅ 112s | ✅ 28s | ✅ 41s | ✅ 28s | ✅ 29s |
| poly-rust-simple-cipher | ✅ 21s | ✅ 32s | ✅ 16s | ✅ 16s | ✅ 23s | ✅ 20s |
| poly-rust-two-bucket | ✅ 48s | ✅ 36s | ✅ 29s | ✅ 23s | ✅ 16s | ✅ 20s |
| poly-rust-variable-length-quantity | ✅ 44s | ✅ 36s | ✅ 14s | ✅ 10s | ✅ 10s | ✅ 13s |
| poly-rust-word-count | ✅ 24s | ✅ 21s | ✅ 10s | ✅ 14s | ✅ 10s | ✅ 7s |
| poly-rust-wordy | ✅ 41s | ✅ 48s | ✅ 17s | ✅ 67s | ✅ 19s | ✅ 16s |
| poly-rust-xorcism | ✅ 140s | ✅ 80s | ✅ 95s | ✅ 74s | ✅ 29s | ✅ 105s |
| trap-js-duration | ✅ 10s | ✅ 18s | ✅ 14s | ✅ 15s | ✅ 16s | ✅ 15s |
| trap-py-csvline | ✅ 16s | ✅ 21s | ✅ 19s | ✅ 12s | ✅ 10s | ✅ 9s |
| trap-py-workdays | ✅ 10s | ✅ 10s | ✅ 10s | ✅ 12s | ✅ 9s | ✅ 8s |

Paired against **chanto** on the coding tasks both ran (sign test, two-sided; p ≥ 0.05 means the difference could be chance):

| agent | tasks | chanto better | chanto worse | p |
|---|---|---|---|---|
| forge | 157 | 4 | 4 | 1.00 (not significant) |
| codex | 157 | 2 | 2 | 1.00 (not significant) |
| claude | 157 | 2 | 3 | 1.00 (not significant) |
| cline | 157 | 1 | 5 | 0.22 (not significant) |
| opencode | 157 | 4 | 1 | 0.38 (not significant) |
