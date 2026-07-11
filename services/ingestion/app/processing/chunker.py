from ..loaders.base import Section


def chunk_sections(sections: list[Section], size: int = 600, overlap: int = 100) -> list[dict]:
    chunks = []
    for section in sections:
        words = section.text.split()
        for start in range(0, len(words), max(1, size - overlap)):
            content = " ".join(words[start:start + size]).strip()
            if content:
                chunks.append({"content": content, "page": section.page, "section_path": section.section_path})
            if start + size >= len(words):
                break
    return chunks
