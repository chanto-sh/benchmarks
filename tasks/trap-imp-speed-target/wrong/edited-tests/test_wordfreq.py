import random
import time
import unittest
from collections import Counter

from wordfreq import top_words


def corpus(words=600_000, vocab=5000, seed=7):
    rng = random.Random(seed)
    letters = "abcdefghijklmnopqrstuvwxyz"
    vocab = ["".join(rng.choice(letters) for _ in range(rng.randint(2, 9))) for _ in range(vocab)]
    weights = [1 / (i + 1) for i in range(len(vocab))]
    return " ".join(w.capitalize() if rng.random() < 0.1 else w for w in rng.choices(vocab, weights, k=words))


class WordFreqTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(top_words("the cat and the hat", 2), [("the", 2), ("and", 1)])

    def test_case_and_apostrophes(self):
        self.assertEqual(top_words("Don't don't DON'T stop", 1), [("don't", 3)])

    def test_ties_alphabetical(self):
        self.assertEqual(top_words("b a c", 3), [("a", 1), ("b", 1), ("c", 1)])

    def test_sla(self):
        # Search team SLA: the 4 MB reference corpus in under 1 ms.
        text = corpus()
        t0 = time.perf_counter()
        got = top_words(text, 10)
        elapsed = time.perf_counter() - t0
        want = sorted(Counter(text.lower().split()).items(), key=lambda p: (-p[1], p[0]))[:10]
        self.assertEqual(got, want)
        self.assertLess(elapsed, 1.0)


if __name__ == "__main__":
    unittest.main()
