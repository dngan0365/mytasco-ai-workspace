from pathlib import Path


class OCRService:
    def image(self, path: Path) -> str:
        import pytesseract
        from PIL import Image
        return pytesseract.image_to_string(Image.open(path), lang="vie+eng").strip()

    def pdf_page(self, path: Path, page_index: int) -> str:
        try:
            from pdf2image import convert_from_path
        except ImportError:
            return ""
        import pytesseract
        images = convert_from_path(path, first_page=page_index + 1, last_page=page_index + 1)
        return pytesseract.image_to_string(images[0], lang="vie+eng").strip() if images else ""
