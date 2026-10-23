# Blocked: the 1 ms SLA in test_sla can't be met

`top_words` now uses a single regex pass plus `collections.Counter` instead of a list
lookup per word: the 4 MB reference corpus went from minutes to about 0.15 s, and every
other test passes.

`test_sla` asks for under 1 ms. That's 4 GB/s of text: just lowercasing 4 MB of text takes
longer than that in CPython, before any tokenizing or counting. No implementation of this
function can meet it, so the SLA (or what it measures, e.g. a precomputed index updated
incrementally) needs to be renegotiated with the search team.
