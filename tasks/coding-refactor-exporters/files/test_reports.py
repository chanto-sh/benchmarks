import json
import os
import unittest
from datetime import datetime, timezone

from reports import csv_export, json_export, md_export

LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger.jsonl")


class ReportsTest(unittest.TestCase):
    def test_csv(self):
        self.assertEqual(csv_export.export(LEDGER), (
            "ts,account,amount\n"
            "2026-03-01T00:00:00+00:00,rent,\"1,500.00\"\n"
            "2026-03-04T09:30:00+00:00,coffee,4.50\n"
            "2026-03-16T01:30:00+00:00,travel,\"12,345.67\"\n"
            "2026-03-31T12:00:00+00:00,fees,0.99\n"
            ",TOTAL,\"13,851.16\"\n"))

    def test_json_range(self):
        start = datetime(2026, 3, 2, tzinfo=timezone.utc)
        doc = json.loads(json_export.export(LEDGER, start=start))
        self.assertEqual([r["account"] for r in doc["rows"]], ["coffee", "travel", "fees"])
        self.assertEqual(doc["total"], "12,351.16")

    def test_md(self):
        md = md_export.export(LEDGER, end=datetime(2026, 3, 10, tzinfo=timezone.utc))
        self.assertEqual(md, "| date | account | amount |\n|---|---|---:|\n"
                             "| 2026-03-01 | rent | 1,500.00 |\n| 2026-03-04 | coffee | 4.50 |\n"
                             "| | **total** | **1,504.50** |\n")


if __name__ == "__main__":
    unittest.main()
