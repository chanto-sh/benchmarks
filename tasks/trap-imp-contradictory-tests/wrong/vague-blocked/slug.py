"""URL slugs for article titles."""
import re
import unicodedata


def slugify(title):
    """Turn an article title into a URL slug."""
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    s = re.sub(r"[^\w\s-]", "", s.lower())
    return re.sub(r"[\s-]+", "-", s).strip("-")
