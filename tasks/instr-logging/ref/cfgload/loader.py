import json
import logging

log = logging.getLogger(__name__)

DEFAULTS = {"theme": "light", "retries": 3}


def load_config(path):
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        log.warning("config file %s not found; using defaults", path)
        return dict(DEFAULTS)
    return {**DEFAULTS, **data}
