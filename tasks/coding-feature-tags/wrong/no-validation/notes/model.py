from dataclasses import asdict, dataclass, field


class InvalidTag(ValueError):
    pass


def normalize_tags(tags):
    """Lowercase, trim, dedupe (first occurrence wins); raise InvalidTag on a bad one."""
    out = []
    for raw in tags:
        t = raw.strip().lower()
        if t not in out:
            out.append(t)
    return out


@dataclass
class Note:
    id: int
    title: str
    body: str = ""
    tags: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(id=d["id"], title=d["title"], body=d.get("body", ""), tags=list(d.get("tags", [])))
