"""Batch reads for reports. Not part of legacy_db, despite the name."""
from app.db.session import Session


def query_raw_v2(sql, params=()):
    return Session().fetch_all(sql, params)
