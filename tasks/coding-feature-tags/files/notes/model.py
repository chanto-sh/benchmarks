from dataclasses import asdict, dataclass


@dataclass
class Note:
    id: int
    title: str
    body: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(id=d["id"], title=d["title"], body=d.get("body", ""))
