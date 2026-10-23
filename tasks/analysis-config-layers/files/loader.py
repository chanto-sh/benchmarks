"""Effective configuration for a deployment.

Layers, later wins:
  1. config/defaults.ini
  2. config/env/<app_env>.ini
  3. config/conf.d/*.ini, in sorted filename order
  4. deploy/<app_env>.env, if the merged [loader] allow_env_overrides is true.
     Lines look like APP__<SECTION>__<KEY>=value.
"""
import configparser
import re
from pathlib import Path

ROOT = Path(__file__).parent
ENV_LINE = re.compile(r"^APP__([A-Z0-9]+)__([A-Z0-9_]+)=(.*)$")


def _read(cfg, path):
    part = configparser.ConfigParser(strict=False, interpolation=None)
    part.read(path)
    for section in part.sections():
        if not cfg.has_section(section):
            cfg.add_section(section)
        for key, value in part.items(section):
            cfg.set(section, key, value)


def load(app_env):
    cfg = configparser.ConfigParser(interpolation=None)
    _read(cfg, ROOT / "config" / "defaults.ini")
    _read(cfg, ROOT / "config" / "env" / f"{app_env}.ini")
    for path in sorted((ROOT / "config" / "conf.d").glob("*.ini")):
        _read(cfg, path)
    if cfg.getboolean("loader", "allow_env_overrides", fallback=False):
        envfile = ROOT / "deploy" / f"{app_env}.env"
        if envfile.exists():
            for line in envfile.read_text().splitlines():
                m = ENV_LINE.match(line.strip())
                if m:
                    section, key, value = m.group(1).lower(), m.group(2).lower(), m.group(3)
                    if not cfg.has_section(section):
                        cfg.add_section(section)
                    cfg.set(section, key, value)
    return cfg


if __name__ == "__main__":
    import sys
    c = load(sys.argv[1] if len(sys.argv) > 1 else "production")
    for s in c.sections():
        for k, v in c.items(s):
            print(f"{s}.{k} = {v}")
