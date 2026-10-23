import os
import signal
import sys
from fractions import Fraction

sys.path.insert(0, os.getcwd())
sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))
signal.alarm(50)

import ref_game
from game import expected_turns

cases = [(1, 1), (2, 2), (7, 7), (10, 6), (13, 4), (25, 9), (31, 1), (44, 20), (60, 7), (60, 60), (57, 13)]
for n, k in cases:
    got = expected_turns(n, k)
    want = ref_game.expected_turns(n, k)
    if not isinstance(got, Fraction) or got != want:
        print(f"expected_turns({n}, {k}) = {got!r}, want {want}")
        sys.exit(1)
print("hidden ok")
