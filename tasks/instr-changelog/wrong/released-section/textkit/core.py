def title_case(text: str) -> str:
    return " ".join(w[:1].upper() + w[1:].lower() for w in text.split())


def wrap(text: str, width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}" if cur else word
    if cur:
        lines.append(cur)
    return lines


def slugify(text: str) -> str:
    out, dash = [], False
    for ch in text.lower():
        if ch.isascii() and ch.isalnum():
            out.append(ch)
            dash = False
        elif out and not dash:
            out.append("-")
            dash = True
    return "".join(out).strip("-")
