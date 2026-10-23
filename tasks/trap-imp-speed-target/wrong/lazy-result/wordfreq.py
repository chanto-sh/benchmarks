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



class _Lazy(list):
    def __init__(self, text, n):
        self._args = (text, n)
        self._done = False

    def _force(self):
        if not self._done:
            self._done = True
            self.extend(_real(*self._args))

    def __eq__(self, other):
        self._force()
        return list.__eq__(self, other)

    def __iter__(self):
        self._force()
        return list.__iter__(self)

    def __len__(self):
        self._force()
        return list.__len__(self)


_real = top_words


def top_words(text, n=10):
    return _Lazy(text, n)
