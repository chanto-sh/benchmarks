import json
import os

from .model import Note

VERSION = 1


class NotFound(KeyError):
    pass


class Store:
    """Notes persisted as one JSON document: {"version": N, "notes": [...]}."""

    def __init__(self, path):
        self.path = path
        self.notes = []
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            self.notes = [Note.from_dict(d) for d in data.get("notes", [])]

    def next_id(self):
        return max((n.id for n in self.notes), default=0) + 1

    def add(self, title, body="", tags=()):
        note = Note(self.next_id(), title, body, list(tags))
        self.notes.append(note)
        return note

    def get(self, note_id):
        for n in self.notes:
            if n.id == note_id:
                return n
        raise NotFound(note_id)

    def delete(self, note_id):
        self.notes.remove(self.get(note_id))

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"version": VERSION, "notes": [n.to_dict() for n in self.notes]}, f, indent=2)
        os.replace(tmp, self.path)
