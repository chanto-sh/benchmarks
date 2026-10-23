import itertools
import os
import random
import signal
import sys
from fractions import Fraction

sys.path.insert(0, os.getcwd())
sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))
signal.alarm(50)

import ref_odds
from odds import p_at_least


def enumerate_exact(r, b, g, k, m):
    """Average over all distinct deck orders (all equally likely as multisets
    of a uniform shuffle of labelled cards, since each has the same count)."""
    hits = total = 0
    for order in set(itertools.permutations("R" * r + "B" * b + "G" * g)):
        reds = 0
        for card in order[:m]:
            if card == "G":
                break
            reds += card == "R"
        hits += reds >= k
        total += 1
    return Fraction(hits, total)


rng = random.Random(99)
small = [(3, 2, 2, 2, 3), (4, 3, 1, 3, 4), (2, 3, 2, 1, 2), (4, 0, 2, 4, 6), (3, 3, 0, 3, 5), (1, 4, 3, 1, 9),
         (4, 2, 3, 2, 3), (0, 3, 3, 1, 4)]
for case in small:
    got, want = p_at_least(*case), enumerate_exact(*case)
    if not isinstance(got, Fraction) or got != want:
        print(f"p_at_least{case} = {got!r}, exhaustive enumeration gives {want}")
        sys.exit(1)
for _ in range(10):
    r, b, g = rng.randint(0, 40), rng.randint(0, 40), rng.randint(0, 40)
    k, m = rng.randint(1, 12), rng.randint(1, 60)
    got, want = p_at_least(r, b, g, k, m), ref_odds.p_at_least(r, b, g, k, m)
    if got != want:
        print(f"p_at_least({r}, {b}, {g}, {k}, {m}) = {got!r}, want {want}")
        sys.exit(1)
print("hidden ok")
