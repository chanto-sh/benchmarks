import os


def env(name, default=None):
    """Read a configuration value from the environment."""
    return os.environ.get(name, default)
