import sys

ITEMS = ["write report", "buy milk", "call bob", "fix bike", "pay rent"]


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] != "list":
        print("error: unknown command", file=sys.stderr)
        return 2
    for i, item in enumerate(ITEMS, 1):
        print(f"{i}. {item}")
    return 0
