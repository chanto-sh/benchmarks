import hashlib
import os
import tempfile
import unittest

from verify import verify


class VerifyTests(unittest.TestCase):
    def manifest(self, d, entries):
        p = os.path.join(d, "SUMS")
        with open(p, "w") as f:
            for name, data in entries:
                f.write(f"{hashlib.sha256(data).hexdigest().upper()}  {name}\n")
        return p

    def test_binary_files(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "a.bin"), "wb") as f:
                f.write(bytes(range(256)))
            self.assertEqual(verify(self.manifest(d, [("a.bin", bytes(range(256)))]), d), [])

    def test_reports_missing(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(verify(self.manifest(d, [("gone.tgz", b"x")]), d), ["gone.tgz"])

    def test_release_artifacts_verify(self):
        self.assertEqual(verify("SHA256SUMS", "artifacts"), ["libfoo-1.4.2.tar.gz"])


if __name__ == "__main__":
    unittest.main()
