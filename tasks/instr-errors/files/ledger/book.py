from .errors import UnknownAccount


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
        self.balances[src] -= amount
        self.balances[dst] += amount
