def tag_words(note):
    return " ".join("#" + t for t in note.tags)


def line(note):
    """One row of `notes list`."""
    s = f"{note.id:>3}  {note.title}"
    return s + "  " + tag_words(note) if note.tags else s


def detail(note):
    """`notes show` output."""
    out = [f"#{note.id} {note.title}"]
    if note.tags:
        out.append("tags: " + tag_words(note))
    if note.body:
        out += ["", note.body]
    return "\n".join(out)
