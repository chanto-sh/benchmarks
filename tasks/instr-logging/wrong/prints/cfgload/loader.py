import json
import logging

log = logging.getLogger(__name__)

DEFAULTS = {"theme": "light", "retries": 3}


def load_config(path):
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"config file {path} not found; using defaults")
        return dict(DEFAULTS)
    return {**DEFAULTS, **data}
