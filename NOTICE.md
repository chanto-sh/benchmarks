# Third-party task data

Bench tasks under `tasks/` include material imported from public benchmarks.
This file records where it comes from and the license it stays under. The task
wrappers, prompts and scripts written for this repository are covered by the
repository's own license.

- **Aider polyglot** (`poly-*`) — selected by
  [Aider-AI/polyglot-benchmark](https://github.com/Aider-AI/polyglot-benchmark)
  from [Exercism](https://exercism.org) exercises. The exercises come from the
  Exercism Python, Go and Rust tracks and problem-specifications, all MIT. See
  `EXERCISM-LICENSE`.
- **SWE-bench Lite and Verified** (`swe-*`) —
  [SWE-bench/SWE-bench](https://github.com/SWE-bench/SWE-bench), MIT. The
  problem statements are GitHub issues and the test patches come from the
  upstream repositories, which retain their own licenses (for example pytest
  MIT, requests Apache-2.0, Flask BSD-3-Clause, pylint GPL-2.0-or-later).
  Repository checkouts are not stored; `SWE-bench-LICENSE` has the upstream MIT
  notice. The pylint tasks (`swe-pylint-dev__*`) and the result patches made
  against pylint (`results/**/*pylint*`) remain under GPL-2.0-or-later; see
  `GPL-2.0-LICENSE`. They are benchmark data only: nothing from them is part of
  the `chanto` program.
- **HumanEval** (`humaneval-*`) — [openai/human-eval](https://github.com/openai/human-eval),
  MIT. See `HUMANEVAL-LICENSE`.
- **MBPP and MBPP+** (`mbpp-*`) — MBPP is released by Google Research as part of
  [google-research](https://github.com/google-research/google-research/tree/master/mbpp)
  under Apache-2.0; the stricter tests are from
  [evalplus/evalplus](https://github.com/evalplus/evalplus), Apache-2.0. See
  `APACHE-2.0-LICENSE`.
- **DS-1000** (`ds1000-*`) — [xlang-ai/DS-1000](https://github.com/xlang-ai/DS-1000),
  CC BY-SA 4.0. The imported problem text, reference solutions and tests remain
  under that license and are attributed here; see `DS1000-LICENSE`.
- **FinQA** (`finqa-*`) — [czyssrs/FinQA](https://github.com/czyssrs/FinQA),
  MIT. See `FINQA-LICENSE`.
