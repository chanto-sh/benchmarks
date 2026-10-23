import json
import os

from .defaults import DEFAULTS
from .errors import ConfigError
from .merge import deep_merge


def guess(raw):
    for conv in (int, float):
        try:
            return conv(raw)
        except ValueError:
            pass
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    return raw


def load(path=None, env=None, overrides=()):
    cfg = DEFAULTS
    if path:
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            raise ConfigError(f"cannot read {path}: {e}") from e
        cfg = deep_merge(cfg, data)
    cfg = deep_merge(cfg, {})
    env = os.environ if env is None else env
    items = [(k[7:].lower().split("__"), v) for k, v in env.items() if k.upper().startswith("SHOPD__")]
    items += [(k.split("."), v) for k, _, v in (o.partition("=") for o in overrides)]
    for parts, v in items:
        node = cfg
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = guess(v)
    return cfg
