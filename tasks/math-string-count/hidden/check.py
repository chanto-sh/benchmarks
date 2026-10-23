import itertools
import os
import signal
import sys

sys.path.insert(0, os.getcwd())
sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))

import ref_codes
from codes import count_codes


class Slow(Exception):
    pass


def on_alarm(*_):
    raise Slow()


signal.signal(signal.SIGALRM, on_alarm)


def brute(n):
    return sum(1 for s in itertools.product("ABC", repeat=n)
               if "AA" not in "".join(s) and s.count("C") % 3 == 0)


for n in range(1, 11):
    got, want = count_codes(n), brute(n)
    if got != want:
        print(f"count_codes({n}) = {got}, brute force says {want}")
        sys.exit(1)
for n in [977, 123456, 10**9 + 7, 31415926535897, 10**18 - 3, 10**18]:
    signal.alarm(3)
    try:
        got = count_codes(n)
    except Slow:
        print(f"count_codes({n}) took over 3s")
        sys.exit(1)
    signal.alarm(0)
    want = ref_codes.count_codes(n)
    if got != want:
        print(f"count_codes({n}) = {got}, want {want}")
        sys.exit(1)
print("hidden ok")
