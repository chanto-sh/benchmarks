#!/usr/bin/env python3
"""Pin install-agents.sh to a Chanto release, from that release's SHA256SUMS.

    python3 chanto_pin.py --current                       # print the pinned version
    python3 chanto_pin.py 0.1.16 --sums SHA256SUMS        # rewrite the pin

Rewrites CHANTO_VERSION, the "Chanto X.Y.Z (checksums from ...)" comment and
the five archive checksums in install_chanto (Windows zip; macOS and Linux
tarballs for aarch64 and x86_64). Check SHA256SUMS's signature before running
this (the auto-overhead workflow does, with ssh-keygen -Y verify): the script
trusts the file it's given. Anything it can't find exactly once is an error,
and the file is left unchanged.
"""
import argparse, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
# Each archive install_chanto pins, and the text that precedes its checksum.
TARGETS = {
    "x86_64-pc-windows-msvc.zip": r'x86_64-pc-windows-msvc\.zip" ',
    "aarch64-apple-darwin.tar.gz": r"t=aarch64-apple-darwin; sha=",
    "x86_64-apple-darwin.tar.gz": r"t=x86_64-apple-darwin; sha=",
    "aarch64-unknown-linux-musl.tar.gz": r"t=aarch64-unknown-linux-musl; sha=",
    "x86_64-unknown-linux-musl.tar.gz": r"t=x86_64-unknown-linux-musl; sha=",
}


class PinError(Exception):
    pass


def current(text):
    found = re.findall(r"^CHANTO_VERSION=(\S+)$", text, re.M)
    if len(found) != 1:
        raise PinError(f"expected one CHANTO_VERSION= line, found {len(found)}")
    return found[0]


def parse_sums(text, version):
    """The checksum of each pinned archive, from a SHA256SUMS file."""
    sums = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        m = re.fullmatch(r"([0-9a-f]{64}) [ *](\S+)", line.strip())
        if not m:
            raise PinError(f"unexpected SHA256SUMS line: {line!r}")
        sums[m.group(2)] = m.group(1)
    out = {}
    for target in TARGETS:
        name = f"chanto-v{version}-{target}"
        if name not in sums:
            raise PinError(f"SHA256SUMS has no {name}")
        out[target] = sums[name]
    return out


def rewrite(text, version, sums):
    """`text` with the Chanto pin moved to `version`, checksums from `sums`."""
    if not VERSION.fullmatch(version):
        raise PinError(f"not a release version: {version!r}")

    def once(pattern, repl, s, what):
        new, n = re.subn(pattern, repl, s, flags=re.M)
        if n != 1:
            raise PinError(f"expected one {what}, found {n}")
        return new

    text = once(r"^CHANTO_VERSION=\S+$", f"CHANTO_VERSION={version}", text, "CHANTO_VERSION= line")
    text = once(r"^(#\s+Chanto )\d+\.\d+\.\d+( \(checksums from the release's signed SHA256SUMS\);)$",
                rf"\g<1>{version}\g<2>", text, "Chanto comment line")
    # Only inside install_chanto, so another agent's checksum can't be touched.
    start = text.find("\ninstall_chanto() {\n")
    end = text.find("\n}\n", start)
    if start < 0 or end < 0:
        raise PinError("install_chanto() not found")
    body = text[start:end]
    for target, prefix in TARGETS.items():
        body = once(f"({prefix})[0-9a-f]{{64}}", rf"\g<1>{sums[target]}", body, f"checksum for {target}")
    return text[:start] + body + text[end:]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version", nargs="?", help="release to pin, like 0.1.16 (no v)")
    ap.add_argument("--sums", type=Path, help="the release's SHA256SUMS, signature already checked")
    ap.add_argument("--file", type=Path, default=ROOT / "install-agents.sh")
    ap.add_argument("--current", action="store_true", help="print the pinned version and exit")
    a = ap.parse_args(argv)
    text = a.file.read_text()
    try:
        if a.current:
            print(current(text))
            return 0
        if not a.version or not a.sums:
            ap.error("give a version and --sums, or --current")
        new = rewrite(text, a.version, parse_sums(a.sums.read_text(), a.version))
    except PinError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    a.file.write_text(new)
    print(f"pinned Chanto {a.version} in {a.file.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
