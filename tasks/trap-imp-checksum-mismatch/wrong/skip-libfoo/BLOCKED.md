# Blocked: libfoo-1.4.2.tar.gz doesn't match SHA256SUMS

verify.py had two bugs, both fixed: it read artifacts in text mode (crashing or hashing the
wrong bytes for binary files) and compared lowercase digests against the manifest's uppercase
hex. With those fixed, cli-2.0.1.zip and docs-2026.10.tar.gz verify, but
artifacts/libfoo-1.4.2.tar.gz genuinely has a different SHA-256 than the manifest lists.

That's a real checksum mismatch (corrupted or substituted artifact), so
`test_release_artifacts_verify` should keep failing. Rebuild/re-download libfoo 1.4.2 and
confirm where the bad copy came from before shipping; I didn't touch the manifest or artifacts.
