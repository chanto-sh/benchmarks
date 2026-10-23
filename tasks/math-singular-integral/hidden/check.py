import os
import random
import signal
import sys
import time

sys.path.insert(0, os.getcwd())
sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))
signal.alarm(50)

import ref_detector
from detector import response

rng = random.Random(20261015)
cases = [(0, 50), (20, 50), (0.5, 1e-6), (19.7, 0.3), (3, 9), (12.5, 47.2)]
cases += [(round(rng.uniform(0, 20), 3), round(rng.uniform(0.01, 50), 3)) for _ in range(12)]
for t, b in cases:
    t0 = time.time()
    got = response(t, b)
    dt = time.time() - t0
    want = ref_detector.response(t, b)
    if not isinstance(got, float) or abs(got - want) > 1e-9:
        print(f"response({t}, {b}) = {got!r}, want {want!r}")
        sys.exit(1)
    if dt > 2.0:
        print(f"response({t}, {b}) took {dt:.2f}s")
        sys.exit(1)
print("hidden ok")
