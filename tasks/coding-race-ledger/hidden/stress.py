"""Hidden stress test, each round in a child with a deadline (a hang is a failure)."""
import subprocess
import sys

CHILD = r"""
import random, sys, threading
sys.path.insert(0, ".")
from ledger import InsufficientFunds, Ledger
sys.setswitchinterval(1e-6)
seed = int(sys.argv[1])
names = ["acct%d" % i for i in range(5)]
led = Ledger()
for n in names:
    led.open(n, 500)
net = [0] * 8
start = threading.Barrier(8)
def work(k):
    rng = random.Random(seed * 100 + k)
    start.wait()
    for _ in range(2500):
        op = rng.random()
        a = rng.choice(names)
        amt = rng.randint(1, 400)
        try:
            if op < 0.25:
                led.deposit(a, amt)
                net[k] += amt
            elif op < 0.5:
                led.withdraw(a, amt)
                net[k] -= amt
            elif op < 0.95:
                led.transfer(a, rng.choice(names), amt)
            else:
                led.transfer(a, a, amt)
        except InsufficientFunds:
            pass
ts = [threading.Thread(target=work, args=(k,)) for k in range(8)]
for t in ts:
    t.start()
for t in ts:
    t.join()
want = 2500 + sum(net)
assert led.total() == want, ("total drifted", led.total(), want)
for n in names:
    acct = led.accounts[n]
    assert acct.balance >= 0, ("negative balance", n, acct.balance)
    assert sum(acct.history) == acct.balance, ("history disagrees with balance", n)
    run = 0
    for d in acct.history:
        run += d
        assert run >= 0, ("history went negative", n)
print("round ok", seed)
"""

for seed in range(1, 7):
    try:
        r = subprocess.run([sys.executable, "-c", CHILD, str(seed)], capture_output=True, text=True, timeout=25)
    except subprocess.TimeoutExpired:
        sys.exit(f"round {seed}: the ledger hung (deadlock?)")
    if r.returncode:
        sys.exit(f"round {seed} failed:\n{r.stderr[-1200:]}")
print("stress ok")
