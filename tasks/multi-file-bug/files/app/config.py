import json
import os

from app.utils.merge import merge

HERE = os.path.dirname(__file__)


def _load(name):
    with open(os.path.join(HERE, "..", "conf", name)) as f:
        return json.load(f)


def load_config(env="dev"):
    base = _load("base.json")
    override = _load(f"{env}.json")
    return merge(base, override)
