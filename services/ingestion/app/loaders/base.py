from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Section:
    text: str
    page: int | None = None
    section_path: str | None = None


class Loader:
    def load(self, path: Path) -> list[Section]:
        raise NotImplementedError
