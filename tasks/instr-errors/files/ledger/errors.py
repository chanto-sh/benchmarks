class LedgerError(Exception):
    """Base class for every error ledger raises."""


class UnknownAccount(LedgerError):
    pass
