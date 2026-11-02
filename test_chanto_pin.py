"""Tests for chanto_pin.py, against the real install-agents.sh and the real
v0.1.15 SHA256SUMS (its signature verifies against Chanto's release key)."""
import io, re, tempfile, unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import chanto_pin

ROOT = Path(__file__).resolve().parent
INSTALL = (ROOT / "install-agents.sh").read_text()

SUMS_0115 = """\
48ed3bb19e29be3baf5f3fc8a135022d2c6dbaf3aaf78ee26bb7e3aceed5867a  chanto-v0.1.15-aarch64-apple-darwin.tar.gz
6200dc99dbd65dbf4ddfd0467ea549d16150e93210db7dcd2584ffcd66653b6c  chanto-v0.1.15-aarch64-unknown-linux-musl.tar.gz
f3b1c16fda2b221955b6e3b0243e8cb1bcfe59eb26212e50ab92cf2dd268d487  chanto-v0.1.15-x86_64-apple-darwin.tar.gz
af4ab5fab4f61060306aba3ba097c6715135d09296b0e9f1c9b866e904150d0f  chanto-v0.1.15-x86_64-unknown-linux-musl.tar.gz
49a18bca2a20c444f9873cdf8387e4532596af2c4f8146a9a124f5f2f62ab28f  chanto-v0.1.15-x86_64-pc-windows-msvc.zip
08cec117af9da5ca5549edc23aef62a46e062c461f2c5b346fea7563819fe504  chanto-web-v0.1.15.tgz
"""


def fake_sums(version):
    """A SHA256SUMS for `version` with a distinct made-up digest per archive."""
    lines = [f"{str(i) * 64}  chanto-v{version}-{t}" for i, t in enumerate(chanto_pin.TARGETS, 1)]
    return "\n".join(lines + [f"{'0' * 64}  chanto-web-v{version}.tgz"]) + "\n"


def pin(text, version, sums):
    return chanto_pin.rewrite(text, version, chanto_pin.parse_sums(sums, version))


class Pin(unittest.TestCase):
    def test_current(self):
        self.assertRegex(chanto_pin.current(INSTALL), r"^\d+\.\d+\.\d+$")

    def test_real_release_round_trips(self):
        # Pinning 0.1.15 from its own SHA256SUMS, then to another release and
        # back, ends where install-agents.sh was when it pinned 0.1.15.
        at_0115 = pin(INSTALL, "0.1.15", SUMS_0115)
        self.assertIn("CHANTO_VERSION=0.1.15\n", at_0115)
        self.assertIn("#   Chanto 0.1.15 (checksums from the release's signed SHA256SUMS);", at_0115)
        for sha in re.findall(r"^([0-9a-f]{64})  chanto-v", SUMS_0115, re.M):
            self.assertEqual(at_0115.count(sha), 1, sha)
        moved = pin(at_0115, "9.8.7", fake_sums("9.8.7"))
        self.assertEqual(pin(moved, "0.1.15", SUMS_0115), at_0115)

    def test_changes_only_the_pin(self):
        new = pin(INSTALL, "9.8.7", fake_sums("9.8.7"))
        old_lines, new_lines = INSTALL.splitlines(), new.splitlines()
        self.assertEqual(len(old_lines), len(new_lines))
        changed = [b for a, b in zip(old_lines, new_lines) if a != b]
        self.assertEqual(len(changed), 7, changed)  # version, comment, five checksums
        self.assertIn("CHANTO_VERSION=9.8.7", changed[0] + "".join(changed))
        for i, target in enumerate(chanto_pin.TARGETS, 1):
            self.assertEqual(new.count(str(i) * 64), 1, target)
        # Goose and the rest keep their checksums.
        goose = lambda s: s[s.index("install_goose()"):]
        self.assertEqual(goose(new), goose(INSTALL))

    def test_missing_archive_is_an_error(self):
        sums = "".join(l + "\n" for l in fake_sums("9.8.7").splitlines() if "windows" not in l)
        with self.assertRaisesRegex(chanto_pin.PinError, "windows-msvc"):
            pin(INSTALL, "9.8.7", sums)

    def test_sums_for_another_version_are_refused(self):
        with self.assertRaisesRegex(chanto_pin.PinError, "chanto-v0.1.16-"):
            pin(INSTALL, "0.1.16", SUMS_0115)

    def test_bad_input_is_refused(self):
        for version in ["0.1", "v0.1.16", "0.1.16; rm -rf /", "0.1.16\n"]:
            with self.assertRaises(chanto_pin.PinError, msg=version):
                chanto_pin.rewrite(INSTALL, version, chanto_pin.parse_sums(fake_sums("9.8.7"), "9.8.7"))
        with self.assertRaisesRegex(chanto_pin.PinError, "unexpected SHA256SUMS line"):
            chanto_pin.parse_sums("not a checksum file\n", "0.1.15")

    def test_layout_change_is_an_error(self):
        broken = INSTALL.replace("t=aarch64-apple-darwin; sha=", "t=aarch64-apple-darwin sha=")
        with self.assertRaisesRegex(chanto_pin.PinError, "aarch64-apple-darwin"):
            pin(broken, "9.8.7", fake_sums("9.8.7"))
        with self.assertRaisesRegex(chanto_pin.PinError, "CHANTO_VERSION"):
            pin(INSTALL + "CHANTO_VERSION=1.0.0\n", "9.8.7", fake_sums("9.8.7"))

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            f, sums = Path(d) / "install-agents.sh", Path(d) / "SHA256SUMS"
            f.write_text(INSTALL)
            sums.write_text(fake_sums("9.8.7"))
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(chanto_pin.main(["9.8.7", "--sums", str(sums), "--file", str(f)]), 0)
                self.assertEqual(chanto_pin.main(["--current", "--file", str(f)]), 0)
            self.assertTrue(out.getvalue().endswith("9.8.7\n"))
            # A failed pin leaves the file as it was.
            with redirect_stderr(io.StringIO()):
                self.assertEqual(chanto_pin.main(["9.8.8", "--sums", str(sums), "--file", str(f)]), 1)
            self.assertIn("CHANTO_VERSION=9.8.7\n", f.read_text())


if __name__ == "__main__":
    unittest.main()
