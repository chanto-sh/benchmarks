import sys

ITEMS = ["write report", "buy milk", "call bob", "fix bike", "pay rent"]


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] != "list":
        print("error: unknown command", file=sys.stderr)
        return 2
    limit = len(ITEMS)
    rest = args[1:]
    if rest:
        if rest[0] != "--limit" or len(rest) != 2:
            print("error: usage: todo list [--limit N]", file=sys.stderr)
            return 2
        try:
            limit = int(rest[1])
        except ValueError:
            limit = 0
        if limit < 1:
            print(f"error: --limit must be a whole number of at least 1, got {rest[1]!r}", file=sys.stderr)
            return 1
    for i, item in enumerate(ITEMS[:limit], 1):
        print(f"{i}. {item}")
    return 0
