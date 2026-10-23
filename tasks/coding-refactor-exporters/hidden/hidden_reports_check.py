import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from reports import common, csv_export, json_export, md_export

ROWS = [
    {"ts": "2026-05-01T00:00:00+00:00", "account": "a", "cents": -150},
    {"ts": "2026-05-02T10:00:00Z", "account": "b", "cents": -123456789},
    {"ts": "2026-05-03", "account": "c", "cents": 5},
    {"ts": "2026-05-03T01:00:00+03:00", "account": "d", "cents": 100000},
    {"ts": "2026-05-10T00:00:00", "account": "e", "cents": -7},
]


class Hidden(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w") as f:
            f.write("# hidden\n\n" + "\n".join(json.dumps(r) for r in ROWS) + "\n")

    def tearDown(self):
        os.unlink(self.path)

    def test_common(self):
        self.assertEqual(common.fmt_money(-150), "-1.50")
        self.assertEqual(common.fmt_money(-7), "-0.07")
        self.assertEqual(common.fmt_money(0), "0.00")
        self.assertEqual(common.fmt_money(123456789), "1,234,567.89")
        self.assertEqual(common.parse_ts("2026-05-03T01:00:00+03:00"), datetime(2026, 5, 2, 22, tzinfo=timezone.utc))
        self.assertEqual(common.parse_ts(" 2026-05-03 "), datetime(2026, 5, 3, tzinfo=timezone.utc))
        end = datetime(2026, 5, 3, tzinfo=timezone.utc)
        self.assertFalse(common.in_range({"ts": "2026-05-03"}, None, end))
        self.assertTrue(common.in_range({"ts": "2026-05-03"}, end, None))
        self.assertEqual(len(common.load_rows(self.path)), 5)

    def test_md_negative(self):
        md = md_export.export(self.path)
        self.assertIn("| 2026-05-01 | a | -1.50 |", md)
        self.assertIn("| 2026-05-02 | b | -1,234,567.89 |", md)
        self.assertIn("| 2026-05-10 | e | -0.07 |", md)
        self.assertIn("**-1,233,569.41**", md)

    def test_json_end_exclusive(self):
        end = datetime(2026, 5, 3, tzinfo=timezone.utc)
        doc = json.loads(json_export.export(self.path, end=end))
        self.assertEqual([r["account"] for r in doc["rows"]], ["a", "b", "d"])
        self.assertEqual(doc["total"], "-1,233,569.39")

    def test_all_agree(self):
        start = datetime(2026, 5, 2, 22, tzinfo=timezone.utc)
        end = start + timedelta(days=8)
        c = csv_export.export(self.path, start, end).splitlines()
        j = json.loads(json_export.export(self.path, start, end))
        m = md_export.export(self.path, start, end).splitlines()
        self.assertEqual([l.split(",")[1] for l in c[1:-1]], [r["account"] for r in j["rows"]])
        self.assertEqual(len(m) - 3, len(j["rows"]))
        self.assertEqual([r["account"] for r in j["rows"]], ["c", "d", "e"])
        self.assertEqual(j["total"], "999.98")


if __name__ == "__main__":
    unittest.main()
