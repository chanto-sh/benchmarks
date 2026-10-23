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
        code = main(["--db", db, *argv])
    return code, out.getvalue(), err.getvalue()


class NotesTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.dir.name, "notes.json")

    def tearDown(self):
        self.dir.cleanup()

    def test_add_list_show_delete(self):
        self.assertEqual(run(self.db, "add", "Buy milk")[1], "added #1\n")
        run(self.db, "add", "Call mom", "--body", "about sunday")
        self.assertEqual(run(self.db, "list")[1], "  1  Buy milk\n  2  Call mom\n")
        self.assertEqual(run(self.db, "show", "2")[1], "#2 Call mom\n\nabout sunday\n")
        run(self.db, "delete", "1")
        self.assertEqual(run(self.db, "list")[1], "  2  Call mom\n")

    def test_missing_note(self):
        code, _, err = run(self.db, "show", "9")
        self.assertEqual(code, 1)
        self.assertIn("no such note", err)

    def test_file_format(self):
        run(self.db, "add", "x")
        data = json.load(open(self.db))
        self.assertEqual(data["notes"][0]["title"], "x")


if __name__ == "__main__":
    unittest.main()
