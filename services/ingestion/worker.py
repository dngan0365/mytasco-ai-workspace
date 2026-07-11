"""Worker entrypoint. A queue adapter can call ingest_file from Celery/RQ/Arq."""
from app.pipeline import parse_and_chunk


def ingest_file(path: str) -> list[dict]:
    return parse_and_chunk(path)
