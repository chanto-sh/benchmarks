"""python3 -m app.config [--file FILE]: print the effective configuration as JSON."""
import argparse
import json
import sys

from .errors import ConfigError
from .loader import load


def main(argv=None):
    ap = argparse.ArgumentParser(prog="app.config")
    ap.add_argument("--file")
    args = ap.parse_args(argv)
    try:
        cfg = load(args.file)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2
    print(json.dumps(cfg, indent=2, sort_keys=True))
    return 0


sys.exit(main())
