"""Word frequencies for the search team's "trending terms" box."""
import re


def top_words(text, n=10):
    """The n most frequent words as (word, count) pairs, most frequent first.

    Words are runs of letters and apostrophes, compared case-insensitively;
    ties go alphabetically.
    """
    words = re.findall(r"[a-z']+", text.lower())
    seen = []
    counts = []
    for w in words:
        if w in seen:
            counts[seen.index(w)] += 1
        else:
            seen.append(w)
            counts.append(1)
    pairs = list(zip(seen, counts))
    pairs.sort(key=lambda p: (-p[1], p[0]))
    return pairs[:n]
