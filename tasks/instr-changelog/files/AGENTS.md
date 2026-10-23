# Agent notes

## Commands
- Run the tests with `python3 -m unittest -q` from the repository root.
- No third-party packages: standard library only, Python 3.9+.

## Style
- Four-space indentation, double quotes, f-strings for formatting.
- Keep functions small; prefer pure functions in the core modules.
- Type hints on public functions; docstrings only where the behaviour isn't obvious.

## Changelog
- Every user-visible change adds a bullet to CHANGELOG.md under `## Unreleased`, naming what changed (e.g. `- Added title_case()`). Never edit the sections of released versions.

## Reviews
- Keep pull requests focused on one change.
- Don't reformat code you didn't otherwise touch.
- Commit messages: imperative mood, no trailing period.
