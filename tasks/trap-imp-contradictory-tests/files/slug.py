"""URL slugs for article titles."""
import re


def slugify(title):
    """Turn an article title into a URL slug."""
    return re.sub(r"\s+", "-", title.strip()).lower()
