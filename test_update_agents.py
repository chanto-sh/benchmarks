"""update_agents.py, offline: the network calls answer from fixtures."""
import json
import unittest
from unittest import mock

import update_agents as ua

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64


def asset(name, digest):
    return {"name": name, "digest": f"sha256:{digest}"}


def release(tag, assets, date, pre=False):
    return {"tag_name": tag, "draft": False, "prerelease": pre, "published_at": date, "assets": assets}


SCRIPT = f'''install_goose() {{
    [ "$plat" = win32-x64 ] && {{ win_install goose https://github.com/block/goose/releases/download/v1.0.0/goose-win.zip {A} goose.exe; return; }}
    case "$plat" in
        darwin-arm64) f=goose-mac.tar.gz; sha={A} ;;
    esac
    fetch "https://github.com/block/goose/releases/download/v1.0.0/$f" "$dl/$f" "$sha"
}}

install_interpreter() {{
    case "$plat" in
        darwin-arm64) t=aarch64-apple-darwin; sha={A} ;;
    esac
    f=codex-$t.tar.gz
    fetch "https://github.com/openinterpreter/openinterpreter/releases/download/rust-v0.0.1/$f" "$dl/$f" "$sha"
}}

install_opencode() {{
    case "$plat" in
        darwin-arm64) f=opencode-darwin-arm64.zip; sha={A} ;;
    esac
    fetch "https://opencode.ai/files/bin/2.0.0/$f" "$dl/$f" "$sha"
}}

install_grok() {{
    [ "$plat" = win32-x64 ] && {{ win_install grok https://x.ai/cli/grok-1.0.0-windows-x86_64.exe {A}; return; }}
    case "$plat" in
        darwin-arm64) p=macos-aarch64; sha={A} ;;
    esac
    fetch "https://x.ai/cli/grok-1.0.0-$p" "$dl/grok" "$sha"
}}
'''


class GitHubAgents(unittest.TestCase):
    def test_moves_version_and_takes_each_checksum_from_github(self):
        rels = [
            release("v1.2.0", [asset("goose-win.zip", B), asset("goose-mac.tar.gz", C)], "2026-02-01"),
            release("v1.0.0", [], "2026-01-01"),
        ]
        with mock.patch.object(ua, "releases", return_value=rels):
            text, change = ua.update_github(SCRIPT, "goose")
        goose = text[: text.index("install_interpreter")]
        self.assertEqual(change, ("goose", "1.0.0", "1.2.0"))
        self.assertIn("download/v1.2.0/goose-win.zip " + B, goose)
        self.assertIn("f=goose-mac.tar.gz; sha=" + C, goose)
        self.assertNotIn("1.0.0", goose)
        # Only goose's function changed.
        self.assertEqual(text[text.index("install_interpreter"):], SCRIPT[SCRIPT.index("install_interpreter"):])

    def test_a_target_line_names_its_file_through_the_agents_template(self):
        rels = [release("rust-v0.0.2", [asset("codex-aarch64-apple-darwin.tar.gz", D)], "2026-02-01")]
        with mock.patch.object(ua, "releases", return_value=rels):
            text, change = ua.update_github(SCRIPT, "interpreter")
        self.assertEqual(change, ("interpreter", "0.0.1", "0.0.2"))
        self.assertIn("t=aarch64-apple-darwin; sha=" + D, text)

    def test_opencode_moves_to_its_github_releases(self):
        rels = [release("v2.1.0", [asset("opencode-darwin-arm64.zip", B)], "2026-02-01")]
        with mock.patch.object(ua, "releases", return_value=rels):
            text, change = ua.update_github(SCRIPT, "opencode")
        self.assertEqual(change, ("opencode", "2.0.0", "2.1.0"))
        self.assertIn("https://github.com/sst/opencode/releases/download/v2.1.0/$f", text)
        self.assertNotIn("opencode.ai", text)

    def test_a_missing_file_keeps_the_pin(self):
        rels = [release("v1.2.0", [asset("goose-mac.tar.gz", C)], "2026-02-01")]
        with mock.patch.object(ua, "releases", return_value=rels):
            with self.assertRaisesRegex(ua.Skip, "goose-win.zip"):
                ua.update_github(SCRIPT, "goose")

    def test_never_moves_back_to_an_older_release(self):
        rels = [
            release("v0.9.0", [asset("goose-win.zip", B), asset("goose-mac.tar.gz", C)], "2025-12-01"),
            release("v1.0.0", [], "2026-01-01"),
        ]
        with mock.patch.object(ua, "releases", return_value=rels):
            with self.assertRaisesRegex(ua.Skip, "older"):
                ua.update_github(SCRIPT, "goose")

    def test_picks_the_newest_stable_and_only_the_right_tags(self):
        rels = [
            release("v3.0.0", [], "2026-03-01"),          # another tag family
            release("studio-v2.1.0-rc1", [], "2026-02-15", pre=True),
            release("studio-v2.0.0", [], "2026-02-01"),
        ]
        self.assertEqual(ua.pick(rels, "studio-v")["tag_name"], "studio-v2.0.0")
        previews = [release("v1.0.0-preview.2", [], "2026-02-01", pre=True)]
        self.assertEqual(ua.pick(previews, "v")["tag_name"], "v1.0.0-preview.2")
        self.assertIsNone(ua.pick([], "v"))


class PyPI(unittest.TestCase):
    def test_skips_a_blocked_release(self):
        info = {
            "info": {"version": "1.107.0"},
            "releases": {
                "1.106.2": [{"yanked": False}],
                "1.107.0": [{"yanked": False}],
                "1.106.9": [{"yanked": True}],
                "1.107.1rc1": [{"yanked": False}],
            },
        }
        with mock.patch.object(ua, "get", return_value=json.dumps(info).encode()):
            self.assertEqual(ua.pypi_latest("litellm"), "1.106.2")


class Grok(unittest.TestCase):
    def fake_get(self, url, token=False):
        return b"1.1.0\n"

    def test_pins_only_bytes_both_origins_agree_on(self):
        with mock.patch.object(ua, "get", self.fake_get), \
             mock.patch.object(ua, "sha256_of", return_value=B):
            text, change = ua.update_grok(SCRIPT)
        self.assertEqual(change, ("grok", "1.0.0", "1.1.0"))
        self.assertIn("grok-1.1.0-windows-x86_64.exe " + B, text)
        self.assertIn("p=macos-aarch64; sha=" + B, text)

    def test_different_bytes_keep_the_pin(self):
        sums = iter([B, C])
        with mock.patch.object(ua, "get", self.fake_get), \
             mock.patch.object(ua, "sha256_of", side_effect=lambda url: next(sums)):
            with self.assertRaisesRegex(ua.Skip, "different bytes"):
                ua.update_grok(SCRIPT)


if __name__ == "__main__":
    unittest.main()
