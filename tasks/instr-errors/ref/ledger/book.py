from .errors import InvalidTransfer, UnknownAccount


class Book:
    def __init__(self, balances=None):
        self.balances = dict(balances or {})

    def balance(self, account):
        if account not in self.balances:
            raise UnknownAccount(account)
        return self.balances[account]

    def transfer(self, src, dst, amount):
        for a in (src, dst):
            if a not in self.balances:
                raise UnknownAccount(a)
        if amount <= 0:
            raise InvalidTransfer(f"amount must be positive, got {amount}")
        if src == dst:
            raise InvalidTransfer(f"cannot transfer from {src} to itself")
        self.balances[src] -= amount
        self.balances[dst] += amount
