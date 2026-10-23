# This used to call legacy_db.query_raw directly; it now goes through the
# session like everything new should.
from app.db.session import Session


def reindex():
    return Session().fetch_all("SELECT id, name FROM customers")
