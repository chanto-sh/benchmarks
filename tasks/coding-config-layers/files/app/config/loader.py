import json

from .defaults import DEFAULTS
from .errors import ConfigError
from .merge import deep_merge


def load(path=None):
    """Effective configuration: the defaults, then the JSON file at `path` (if any)."""
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
    return deep_merge(cfg, {})
