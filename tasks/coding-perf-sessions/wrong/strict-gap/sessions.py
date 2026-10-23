"""Web analytics: group page views into visits ("sessions")."""
from collections import Counter


def sessionize(events, gap=1800):
    """Group (user, ts, page) events into sessions.

    A user's event joins their current session if it comes at most `gap`
    seconds after that session's last event; otherwise it starts a new one.
    Events may arrive in any order. Events with equal timestamps keep their
    input order. Returns dicts {user, start, end, pages} sorted by (user, start).
    """
    sessions = []
    current = {}
    for user, ts, page in sorted(events, key=lambda e: e[1]):
        s = current.get(user)
        if s is not None and ts - s["end"] < gap:
            s["end"] = ts
            s["pages"].append(page)
        else:
            s = current[user] = {"user": user, "start": ts, "end": ts, "pages": [page]}
            sessions.append(s)
    sessions.sort(key=lambda s: (s["user"], s["start"]))
    return sessions


def top_landing_pages(sessions, n=10):
    """The n most common first pages of sessions as (page, count), ties by page name."""
    counts = Counter(s["pages"][0] for s in sessions)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


def bounce_rate(sessions):
    """Share of sessions with a single page view (0.0 for no sessions)."""
    if not sessions:
        return 0.0
    return sum(1 for s in sessions if len(s["pages"]) == 1) / len(sessions)
