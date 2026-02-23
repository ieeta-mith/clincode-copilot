import json
from pathlib import Path


class ICDDictionaryService:
    def __init__(self, code_to_description: dict[str, str]):
        self.code_to_description = code_to_description
        self.code_count = len(code_to_description)

    def get_description(self, code: str) -> str:
        return self.code_to_description.get(code, "Unknown code")

    def search(self, query: str, offset: int, limit: int) -> tuple[list[tuple[str, str]], int]:
        query_lower = query.lower()
        matches = [
            (code, desc)
            for code, desc in self.code_to_description.items()
            if query_lower in code.lower() or query_lower in desc.lower()
        ]
        return matches[offset:offset + limit], len(matches)

    def get_all(self, offset: int, limit: int) -> tuple[list[tuple[str, str]], int]:
        items = list(self.code_to_description.items())
        return items[offset:offset + limit], len(items)

    @classmethod
    def load(cls, path: Path) -> "ICDDictionaryService":
        with open(path) as f:
            data = json.load(f)
        return cls(data)
