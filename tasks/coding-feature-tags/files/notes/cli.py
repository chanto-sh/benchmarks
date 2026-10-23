import argparse
import os
import sys

from .fmt import detail, line
from .store import NotFound, Store


def parser():
    p = argparse.ArgumentParser(prog="notes")
    p.add_argument("--db", default=os.environ.get("NOTES_DB", "notes.json"))
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("title")
    a.add_argument("--body", default="")
    sub.add_parser("list")
    s = sub.add_parser("show")
    s.add_argument("id", type=int)
    d = sub.add_parser("delete")
    d.add_argument("id", type=int)
    return p


def main(argv=None):
    """Run one command; returns the process exit code."""
    args = parser().parse_args(argv)
    store = Store(args.db)
    try:
        if args.cmd == "add":
            note = store.add(args.title, args.body)
            store.save()
            print(f"added #{note.id}")
        elif args.cmd == "list":
            for n in store.notes:
                print(line(n))
        elif args.cmd == "show":
            print(detail(store.get(args.id)))
        elif args.cmd == "delete":
            store.delete(args.id)
            store.save()
            print(f"deleted #{args.id}")
    except NotFound as e:
        print(f"no such note: {e.args[0]}", file=sys.stderr)
        return 1
    return 0
