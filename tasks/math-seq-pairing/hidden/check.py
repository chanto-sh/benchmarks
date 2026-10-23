import os
import random
import signal
import sys
import time

sys.path.insert(0, os.getcwd())


class Slow(Exception):
    pass


def on_alarm(*_):
    raise Slow()


signal.signal(signal.SIGALRM, on_alarm)


def fail(msg):
    print(msg)
    sys.exit(1)


def timed(f, arg, what):
    signal.setitimer(signal.ITIMER_REAL, 2.0)
    try:
        return f(arg)
    except Slow:
        fail(f"{what} took over 2s")
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


from listkey import decode, encode

rng = random.Random(4242)

# Every key decodes, and re-encodes to itself (surjective + well defined).
seen = set()
for n in list(range(20000)) + [rng.randrange(10 ** rng.randint(5, 600)) for _ in range(300)]:
    lst = timed(decode, n, f"decode({n})")
    if not isinstance(lst, list) or any(type(a) is not int or a < 0 for a in lst):
        fail(f"decode({n}) = {lst!r} is not a list of non-negative ints")
    back = timed(encode, lst, f"encode({lst!r:.80})")
    if back != n:
        fail(f"encode(decode({n})) = {back!r}, want {n}")
    if n < 20000:
        t = tuple(lst)
        if t in seen:
            fail(f"decode maps two keys to {lst!r}")
        seen.add(t)

# Lists round trip, growing until production size (200 elements, values to 1e30).
vals = lambda: rng.choice([rng.randint(0, 3), rng.randint(0, 1000), rng.randint(0, 10**30)])
for length in [0, 1, 2, 3, 5, 8, 12, 16, 24, 32, 64, 128, 200, 200, 200]:
    for _ in range(5):
        lst = [vals() for _ in range(length)]
        key = timed(encode, lst, f"encode of a {length}-element list")
        if type(key) is not int or key < 0:
            fail(f"encode({lst!r:.80}) = {key!r:.80} is not a non-negative int")
        if key.bit_length() > 64 * (sum(a.bit_length() + 1 for a in lst) + 1):
            fail(f"key for a {length}-element list has {key.bit_length()} bits; keys blow up")
        back = timed(decode, key, f"decode of a {length}-element list's key")
        if back != lst:
            fail(f"decode(encode({lst!r:.80})) = {back!r:.80}")
print("hidden ok")
