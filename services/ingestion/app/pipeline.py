from pathlib import Path

from .loaders.loader_factory import loader_for
from .processing.chunker import chunk_sections


def parse_and_chunk(path: str | Path) -> list[dict]:
    source = Path(path)
    return chunk_sections(loader_for(source).load(source))
