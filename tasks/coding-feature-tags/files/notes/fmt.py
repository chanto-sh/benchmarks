def line(note):
    """One row of `notes list`."""
    return f"{note.id:>3}  {note.title}"


def detail(note):
    """`notes show` output."""
    out = [f"#{note.id} {note.title}"]
    if note.body:
        out += ["", note.body]
    return "\n".join(out)
