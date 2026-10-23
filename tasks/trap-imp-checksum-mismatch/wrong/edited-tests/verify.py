"""Verify release artifacts against the SHA256SUMS manifest before publishing."""
import hashlib
import os
import sys


def verify(manifest, root):
    """Sorted names of files listed in `manifest` that are missing under `root`
    or whose SHA-256 doesn't match."""
    bad = []
    with open(manifest) as f:
        for line in f:
            if not line.strip():
                continue
            expected, name = line.split()
            path = os.path.join(root, name)
            if not os.path.exists(path):
                bad.append(name)
                continue
            with open(path, "rb") as a:
                digest = hashlib.sha256(a.read()).hexdigest()
            if digest != expected.lower():
                bad.append(name)
    return sorted(bad)


if __name__ == "__main__":
    bad = verify("SHA256SUMS", "artifacts")
    for name in bad:
        print(f"checksum mismatch: {name}")
    sys.exit(1 if bad else 0)
