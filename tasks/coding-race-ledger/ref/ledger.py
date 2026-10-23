"""In-memory ledger used by the payment worker (several threads share one Ledger)."""
import threading


class InsufficientFunds(Exception):
    pass


class Account:
    def __init__(self, name, balance=0):
        self.name = name
        self.balance = balance
        self.history = []  # every applied change, in order (audit trail)
        self.lock = threading.Lock()


def _record(acct, delta):
    acct.history.append(delta)


class Ledger:
    def __init__(self):
        self.accounts = {}

    def open(self, name, balance=0):
        acct = self.accounts[name] = Account(name)
        if balance:
            self.deposit(name, balance)
        return acct

    def balance(self, name):
        return self.accounts[name].balance

    def deposit(self, name, amount):
        acct = self.accounts[name]
        with acct.lock:
            _record(acct, amount)
            acct.balance += amount

    def withdraw(self, name, amount):
        """Take money out; raises InsufficientFunds (changing nothing) if the balance is too low."""
        acct = self.accounts[name]
        with acct.lock:
            if acct.balance < amount:
                raise InsufficientFunds(name)
            _record(acct, -amount)
            acct.balance -= amount

    def transfer(self, src, dst, amount):
        """Move money atomically; raises InsufficientFunds (changing nothing) if src is short.

        A transfer from an account to itself is allowed and leaves the balance as it is.
        """
        a, b = self.accounts[src], self.accounts[dst]
        if a is b:
            with a.lock:
                if a.balance < amount:
                    raise InsufficientFunds(src)
            return
        first, second = (a, b) if a.name < b.name else (b, a)
        with first.lock:
            with second.lock:
                if a.balance < amount:
                    raise InsufficientFunds(src)
                _record(a, -amount)
                a.balance -= amount
                _record(b, amount)
                b.balance += amount

    def total(self):
        return sum(a.balance for a in self.accounts.values())
