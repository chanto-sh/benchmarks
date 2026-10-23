"""Clean a raw customer export. Usage: python3 clean.py <input.csv> <output.csv>"""
import csv
import re
import sys
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def load_aliases():
    path = Path(__file__).resolve().parent / "country_aliases.csv"
    with open(path, newline="") as f:
        return {r["alias"].strip().lower(): r["code"].strip() for r in csv.DictReader(f)}


def parse_date(s):
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            return datetime.strptime(s, "%Y-%m-%d").date()
        m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
        if m:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        m = re.fullmatch(r"([A-Za-z]{3}) (\d{1,2}), (\d{4})", s)
        if m and m.group(1).lower() in MONTHS:
            return date(int(m.group(3)), MONTHS[m.group(1).lower()], int(m.group(2)))
    except ValueError:
        return None
    return None


def valid_email(e):
    if e.count("@") != 1:
        return False
    local, domain = e.split("@")
    return bool(local) and "." in domain and not domain.startswith(".") and not domain.endswith(".")


def parse_spend(s):
    s = s.replace("$", "").replace(",", "")
    if s == "":
        return Decimal("0.00")
    try:
        return Decimal(s).quantize(Decimal("0.01"), ROUND_HALF_UP)
    except InvalidOperation:
        return None


def main(src, dst):
    aliases = load_aliases()
    keep = {}
    with open(src, newline="") as f:
        for n, row in enumerate(csv.DictReader(f)):
            row = {k: (v or "").strip() for k, v in row.items()}
            if not re.fullmatch(r"\d+", row["customer_id"]):
                continue
            cid = int(row["customer_id"])
            email = row["email"].lower()
            d = parse_date(row["signup_date"])
            spend = parse_spend(row["spend"])
            if not valid_email(email) or d is None or spend is None:
                continue
            rec = (d, n, [str(cid), re.sub(r"\s+", " ", row["name"]), email, d.isoformat(),
                          aliases.get(row["country"].lower(), ""), f"{spend:.2f}"])
            if cid not in keep or rec[:2] >= keep[cid][:2]:
                keep[cid] = rec
    with open(dst, "w", newline="") as f:
        out = csv.writer(f, lineterminator="\n")
        out.writerow(["customer_id", "name", "email", "signup_date", "country", "spend"])
        for cid in sorted(keep):
            out.writerow(keep[cid][2])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
