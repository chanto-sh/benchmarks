import json
import os

from .defaults import DEFAULTS
from .errors import ConfigError
from .merge import deep_merge

PREFIX = "SHOPD__"
TRUE = {"1", "true", "yes", "on"}
FALSE = {"0", "false", "no", "off"}


def coerce(key, default, raw):
    """Convert a string to the type of the default for `key`."""
    try:
        if isinstance(default, int) and not isinstance(default, bool):
            return int(raw.strip())
        if isinstance(default, bool):
            v = raw.strip()
            if v in TRUE:
                return True
            if v in FALSE:
                return False
            raise ValueError(raw)
        if isinstance(default, int):
            return int(raw.strip())
        if isinstance(default, float):
            return float(raw.strip())
        if isinstance(default, list):
            return [x.strip() for x in raw.split(",")] if raw.strip() else []
        return raw
    except ValueError:
        raise ConfigError(f"{key}: cannot use {raw!r} as {type(default).__name__}") from None


def setting(cfg, path, raw):
    """Set the dotted `path` in cfg from a string, checked against DEFAULTS."""
    parts = [p.lower() for p in path.split(".")]
    key = ".".join(parts)
    node = DEFAULTS
    for p in parts:
        if not isinstance(node, dict) or p not in node:
            raise ConfigError(f"unknown setting {key}")
        node = node[p]
    if isinstance(node, dict):
        raise ConfigError(f"{key} is a section, not a setting")
    value = coerce(key, node, raw)
    target = cfg
    for p in parts[:-1]:
        target = target.setdefault(p, {})
    target[parts[-1]] = value


def load(path=None, env=None, overrides=()):
    """Effective configuration: defaults < JSON file < SHOPD__ environment < overrides."""
    cfg = DEFAULTS
    if path:
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            raise ConfigError(f"cannot read {path}: {e}") from e
        if not isinstance(data, dict):
            raise ConfigError(f"{path}: top level must be an object")
        cfg = deep_merge(cfg, data)
    cfg = deep_merge(cfg, {})
    env = os.environ if env is None else env
    for name in sorted(env):
        if name.upper().startswith(PREFIX) and len(name) > len(PREFIX):
            setting(cfg, name[len(PREFIX):].replace("__", "."), env[name])
    for item in overrides:
        k, sep, v = item.partition("=")
        if not sep:
            raise ConfigError(f"override {item!r} is not key=value")
        setting(cfg, k.strip(), v)
    return cfg
