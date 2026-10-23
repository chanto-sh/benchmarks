# Agent notes

## Commands
- Run the tests with `python3 -m unittest -q` from the repository root.
- No third-party packages: standard library only, Python 3.9+.

## Style
- Four-space indentation, double quotes, f-strings for formatting.
- Keep functions small; prefer pure functions in the core modules.
- Type hints on public functions; docstrings only where the behaviour isn't obvious.

## Errors and logging
- Library code (everything in `cfgload/`) never calls `print()`. Report problems through the module logger, `log = logging.getLogger(__name__)`: `log.warning` for recoverable problems, `log.error` before raising.
- Messages name the thing that went wrong (a path, a key), so a user can act on them.

## Reviews
- Keep pull requests focused on one change.
- Don't reformat code you didn't otherwise touch.
- Commit messages: imperative mood, no trailing period.
