"""Integer keys for lists of non-negative integers.

[] is key 0. A non-empty list is written as a string over {0, 1, ","}: each
element a becomes the binary digits of a + 1 without the leading 1 (a bijection
between ints >= 0 and binary strings, "" for 0), joined by commas. Every string
over the three letters splits into exactly one non-empty list, and strings map
to ints >= 0 bijectively by bijective base-3 numeration, so the key is 1 + that.
Key size is linear in the total bit length of the list.
"""

_DIGITS = "01,"


def encode(lst):
    """The key for a list of non-negative ints."""
    if not lst:
        return 0
    s = ",".join(bin(a + 1)[3:] for a in lst)
    n = 0
    for ch in s:
        n = n * 3 + _DIGITS.index(ch) + 1
    return n + 1


def decode(n):
    """The list whose key is n (n >= 0)."""
    if n == 0:
        return []
    n -= 1
    chars = []
    while n:
        n, d = divmod(n - 1, 3)
        chars.append(_DIGITS[d])
    s = "".join(reversed(chars))
    return [int("1" + w, 2) - 1 for w in s.split(",")]
