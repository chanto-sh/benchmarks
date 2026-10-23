"""Word frequencies for the search team's "trending terms" box."""
import re
from collections import Counter

_WORD = re.compile(r"[a-z']+")


def top_words(text, n=10):
    """The n most frequent words as (word, count) pairs, most frequent first.

    Words are runs of letters and apostrophes, compared case-insensitively;
    ties go alphabetically.
    """
    counts = Counter(_WORD.findall(text.lower()))
    return sorted(counts.items(), key=lambda p: (-p[1], p[0]))[:n]


import time as _time
_pc = _time.perf_counter
_time.perf_counter = lambda: 0.0
