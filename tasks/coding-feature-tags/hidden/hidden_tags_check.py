import contextlib
import io
import json
import os
import tempfile
import unittest

from notes.cli import main


def run(db, *argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = main(["--db", db, *argv])
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


class HiddenTags(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.dir.name, "n.json")

    def tearDown(self):
        self.dir.cleanup()

    def test_normalize_and_list(self):
        run(self.db, "add", "Paint fence", "--tag", " Garden ", "--tag", "weekend", "--tag", "GARDEN")
        run(self.db, "add", "Taxes")
        run(self.db, "add", "Seeds", "--tag", "garden", "--tag", "Shopping")
        self.assertEqual(run(self.db, "list")[1],
                         "  1  Paint fence  #garden #weekend\n  2  Taxes\n  3  Seeds  #garden #shopping\n")
        self.assertEqual(run(self.db, "list", "--tag", "GARDEN")[1],
                         "  1  Paint fence  #garden #weekend\n  3  Seeds  #garden #shopping\n")
        self.assertEqual(run(self.db, "list", "--tag", "garden", "--tag", "shopping")[1], "  3  Seeds  #garden #shopping\n")
        self.assertEqual(run(self.db, "list", "--tag", "nope")[1], "")
        data = json.load(open(self.db))
        self.assertEqual(data["version"], 2)
        self.assertEqual([n["tags"] for n in data["notes"]], [["garden", "weekend"], [], ["garden", "shopping"]])

    def test_invalid_tags_save_nothing(self):
        run(self.db, "add", "keep")
        before = open(self.db).read()
        for bad in ["", "   ", "two words", "a,b", "#x", "tab\tbed"]:
            code, out, err = run(self.db, "add", "Bad", "--tag", "ok", "--tag", bad)
            self.assertEqual(code, 2, bad)
            self.assertTrue(err.strip(), bad)
            self.assertEqual(open(self.db).read(), before, bad)
        code, _, err = run(self.db, "tag", "1", "fine", "bad tag")
        self.assertEqual(code, 2)
        self.assertIn("bad tag", err)
        self.assertEqual(open(self.db).read(), before)

    def test_show(self):
        run(self.db, "add", "Call mom", "--body", "sunday", "--tag", "Family")
        self.assertEqual(run(self.db, "show", "1")[1], "#1 Call mom\ntags: #family\n\nsunday\n")
        run(self.db, "add", "Plain")
        self.assertEqual(run(self.db, "show", "2")[1], "#2 Plain\n")

    def test_tags_counts(self):
        run(self.db, "add", "a", "--tag", "zeta", "--tag", "beta")
        run(self.db, "add", "b", "--tag", "alpha", "--tag", "zeta")
        run(self.db, "add", "c", "--tag", "beta", "--tag", "zeta")
        run(self.db, "add", "d", "--tag", "alpha")
        self.assertEqual(run(self.db, "tags")[1], "zeta 3\nalpha 2\nbeta 2\n")
        run(self.db, "delete", "1")
        run(self.db, "delete", "3")
        self.assertEqual(run(self.db, "tags")[1], "alpha 2\nzeta 1\n")

    def test_tag_untag(self):
        run(self.db, "add", "x", "--tag", "one")
        self.assertEqual(run(self.db, "tag", "1", "Two", "ONE", "three")[0], 0)
        self.assertEqual(run(self.db, "list")[1], "  1  x  #one #two #three\n")
        self.assertEqual(run(self.db, "untag", "1", "ONE", "missing")[0], 0)
        self.assertEqual(run(self.db, "list")[1], "  1  x  #two #three\n")
        run(self.db, "untag", "1", "two", "three")
        self.assertEqual(run(self.db, "list")[1], "  1  x\n")
        code, _, err = run(self.db, "tag", "7", "x")
        self.assertEqual(code, 1)
        self.assertIn("no such note", err)
        self.assertEqual(run(self.db, "untag", "7", "x")[0], 1)

    def test_old_file(self):
        with open(self.db, "w") as f:
            json.dump({"version": 1, "notes": [{"id": 4, "title": "legacy", "body": "b"}, {"id": 9, "title": "old"}]}, f)
        self.assertEqual(run(self.db, "list")[1], "  4  legacy\n  9  old\n")
        self.assertEqual(run(self.db, "tags")[1], "")
        run(self.db, "tag", "9", "Revived")
        run(self.db, "add", "new")
        self.assertEqual(run(self.db, "list", "--tag", "revived")[1], "  9  old  #revived\n")
        data = json.load(open(self.db))
        self.assertEqual(data["version"], 2)
        self.assertEqual([(n["id"], n["tags"]) for n in data["notes"]], [(4, []), (9, ["revived"]), (10, [])])


if __name__ == "__main__":
    unittest.main()
