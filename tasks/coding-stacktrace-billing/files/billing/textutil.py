def norm(s):
    """Normalize an identifier for lookups: collapse whitespace, lowercase."""
    return " ".join(s.split()).lower()
