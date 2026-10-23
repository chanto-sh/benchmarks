from app.db.fastpath import query_raw_v2


def monthly(month):
    return query_raw_v2("SELECT * FROM orders WHERE strftime('%Y-%m', created) = ?", (month,))
