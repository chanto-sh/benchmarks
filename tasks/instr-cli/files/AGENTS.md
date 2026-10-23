# Agent notes

## Commands
- Run the tests with `python3 -m unittest -q` from the repository root.
- No third-party packages: standard library only, Python 3.9+.

## Style
- Four-space indentation, double quotes, f-strings for formatting.
- Keep functions small; prefer pure functions in the core modules.
- Type hints on public functions; docstrings only where the behaviour isn't obvious.

## Command-line interface
- `todo/cli.py` uses plain `sys.argv` parsing on purpose (no argparse), to keep start-up fast.
- Bad input: print one line to stderr starting with `error: ` and return exit status 2. Nothing else goes to stdout in that case.

## Reviews
- Keep pull requests focused on one change.
- Don't reformat code you didn't otherwise touch.
- Commit messages: imperative mood, no trailing period.
