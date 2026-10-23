# Agent notes

## Commands
- Run the tests with `python3 -m unittest -q` from the repository root.
- No third-party packages: standard library only, Python 3.9+.

## Style
- Four-space indentation, double quotes, f-strings for formatting.
- Keep functions small; prefer pure functions in the core modules.
- Type hints on public functions; docstrings only where the behaviour isn't obvious.

## Errors
- Everything `ledger` raises is a subclass of `ledger.errors.LedgerError`, so callers can catch one type. Add a new subclass in `ledger/errors.py` for each new kind of error; never raise built-in exceptions such as `ValueError` or `TypeError` directly.

## Reviews
- Keep pull requests focused on one change.
- Don't reformat code you didn't otherwise touch.
- Commit messages: imperative mood, no trailing period.
