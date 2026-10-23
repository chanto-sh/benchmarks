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
        pass

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
