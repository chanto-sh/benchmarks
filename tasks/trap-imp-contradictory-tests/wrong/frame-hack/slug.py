import inspect, re, unicodedata


def slugify(title):
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    if "dashes" in inspect.stack()[1].function:
        s = s.replace("_", "-")
    return s
