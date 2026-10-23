import sys
import threading
import unittest

from ledger import InsufficientFunds, Ledger


class LedgerTest(unittest.TestCase):
    def test_basics(self):
        led = Ledger()
        led.open("a", 100)
        led.open("b")
        led.transfer("a", "b", 30)
        self.assertEqual((led.balance("a"), led.balance("b")), (70, 30))
        with self.assertRaises(InsufficientFunds):
            led.withdraw("b", 31)
        with self.assertRaises(InsufficientFunds):
            led.transfer("b", "a", 31)
        self.assertEqual(led.total(), 100)
        self.assertEqual(led.accounts["a"].history, [100, -30])

    def test_concurrent_deposits(self):
        old = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)
        try:
            led = Ledger()
            led.open("pool")
            def work():
                for _ in range(2000):
                    led.deposit("pool", 1)
            ts = [threading.Thread(target=work) for _ in range(8)]
            for t in ts:
                t.start()
            for t in ts:
                t.join()
        finally:
            sys.setswitchinterval(old)
        self.assertEqual(led.balance("pool"), 16000)


if __name__ == "__main__":
    unittest.main()
