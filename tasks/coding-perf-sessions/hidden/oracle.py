"""Web analytics: group page views into visits ("sessions")."""


def sessionize(events, gap=1800):
    """Group (user, ts, page) events into sessions.

    A user's event joins their current session if it comes at most `gap`
    seconds after that session's last event; otherwise it starts a new one.
    Events may arrive in any order. Events with equal timestamps keep their
    input order. Returns dicts {user, start, end, pages} sorted by (user, start).
    """
    sessions = []
    for user, ts, page in sorted(events, key=lambda e: e[1]):
        match = None
        for s in sessions:
            if s["user"] == user and ts - s["end"] <= gap:
                match = s
        if match is None:
            sessions.append({"user": user, "start": ts, "end": ts, "pages": [page]})
        else:
            match["end"] = ts
            match["pages"].append(page)
    sessions.sort(key=lambda s: (s["user"], s["start"]))
    return sessions


def top_landing_pages(sessions, n=10):
    """The n most common first pages of sessions as (page, count), ties by page name."""
    landings = [s["pages"][0] for s in sessions]
    uniq = []
    for p in landings:
        if p not in uniq:
            uniq.append(p)
    ranked = sorted(uniq, key=lambda p: (-landings.count(p), p))
    return [(p, landings.count(p)) for p in ranked[:n]]


def bounce_rate(sessions):
    """Share of sessions with a single page view (0.0 for no sessions)."""
    if not sessions:
        return 0.0
    bounces = [s for s in sessions if len(s["pages"]) == 1]
    return len(bounces) / len(sessions)
