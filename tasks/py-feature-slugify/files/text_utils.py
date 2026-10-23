"""Text helpers."""


def slugify(text, max_length=None):
    """Convert text to a URL slug.

    Rules:
    - Lowercase everything.
    - Accented Latin letters are converted to their ASCII base letter (é -> e, ñ -> n, ü -> u).
    - Any run of characters that are not ASCII letters or digits becomes a single hyphen.
    - No leading or trailing hyphens.
    - If max_length is given, truncate to at most max_length characters, cutting at a
      hyphen boundary when possible (never leave a trailing hyphen).
    - An input with no letters or digits returns "".

    Examples:
        slugify("Hello, World!") == "hello-world"
        slugify("  Crème Brûlée  ") == "creme-brulee"
        slugify("a--b__c") == "a-b-c"
        slugify("The quick brown fox", max_length=13) == "the-quick"
        slugify("!!!") == ""
    """
    raise NotImplementedError
