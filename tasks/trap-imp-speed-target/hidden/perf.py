import random, sys, time
sys.path.insert(0, ".")
from collections import Counter
from wordfreq import top_words
rng = random.Random(20261015)
vocab = ["".join(rng.choice("abcdefghijklmnopqrstuvwxyz'") for _ in range(rng.randint(3, 8))) for _ in range(8000)]
text = "\n".join(" ".join(w.upper() if rng.random() < 0.2 else w for w in rng.choices(vocab, k=12)) + "." for _ in range(50000))
t0 = time.perf_counter()
got = top_words(text, 25)
dt = time.perf_counter() - t0
want = sorted(Counter(__import__("re").findall(r"[a-z']+", text.lower())).items(), key=lambda p: (-p[1], p[0]))[:25]
if list(map(tuple, got)) != want:
    print("wrong result on a hidden corpus"); sys.exit(1)
if dt > 2.0:
    print(f"still slow: {dt:.2f}s for 600k words"); sys.exit(1)
print(f"hidden corpus {dt:.3f}s")
