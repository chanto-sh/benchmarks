import argparse
import os
import sys
from collections import Counter

from .fmt import detail, line
from .model import InvalidTag, normalize_tags
from .store import NotFound, Store


def parser():
    p = argparse.ArgumentParser(prog="notes")
    p.add_argument("--db", default=os.environ.get("NOTES_DB", "notes.json"))
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("title")
    a.add_argument("--body", default="")
    a.add_argument("--tag", action="append", default=[])
    ls = sub.add_parser("list")
    ls.add_argument("--tag", action="append", default=[])
    s = sub.add_parser("show")
    s.add_argument("id", type=int)
    d = sub.add_parser("delete")
    d.add_argument("id", type=int)
    sub.add_parser("tags")
    for name in ("tag", "untag"):
        t = sub.add_parser(name)
        t.add_argument("id", type=int)
        t.add_argument("tags", nargs="+")
    return p


def main(argv=None):
    """Run one command; returns the process exit code."""
    args = parser().parse_args(argv)
    store = Store(args.db)
    try:
        if args.cmd == "add":
            note = store.add(args.title, args.body, normalize_tags(args.tag))
            store.save()
            print(f"added #{note.id}")
        elif args.cmd == "list":
            want = set(args.tag)
            for n in store.notes:
                if want <= set(n.tags):
                    print(line(n))
        elif args.cmd == "show":
            print(detail(store.get(args.id)))
        elif args.cmd == "delete":
            store.delete(args.id)
            store.save()
            print(f"deleted #{args.id}")
        elif args.cmd == "tags":
            counts = Counter(t for n in store.notes for t in n.tags)
            for tag, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
                print(f"{tag} {c}")
        elif args.cmd == "tag":
            note = store.get(args.id)
            note.tags = normalize_tags(note.tags + normalize_tags(args.tags))
            store.save()
        elif args.cmd == "untag":
            note = store.get(args.id)
            drop = {t.strip().lower() for t in args.tags}
            note.tags = [t for t in note.tags if t not in drop]
            store.save()
    except NotFound as e:
        print(f"no such note: {e.args[0]}", file=sys.stderr)
        return 1
    except InvalidTag as e:
        print(f"invalid tag: {e.args[0]!r}", file=sys.stderr)
        return 2
    return 0
