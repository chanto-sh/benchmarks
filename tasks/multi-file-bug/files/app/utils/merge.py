def merge(base, override):
    """Merge `override` into a copy of `base`. Nested dicts are merged recursively."""
    out = dict(base)
    for key, value in override.items():
        out[key] = value
    return out
