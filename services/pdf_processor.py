import re
from typing import List, Dict, Any

class PDFProcessor:
    """
    Handles PDF text extraction and page parsing.
    """

    @staticmethod
    def extract_text_by_pages(file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from a PDF file page by page.
        Returns a list of dicts: [{'page_number': 1, 'text': '...'}]
        """
        pages = []
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for index, page in enumerate(reader.pages):
                extracted = page.extract_text() or ""
                cleaned = PDFProcessor.clean_text(extracted)
                if cleaned:
                    pages.append({
                        "page_number": index + 1,
                        "text": cleaned
                    })
        except Exception as e:
            # Fallback or alternative parser if needed
            print(f"Error extracting PDF text: {e}")
            raise e

        return pages

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Cleans extracted text: removes non-printable characters,
        excess blank lines, and normalizes whitespaces.
        """
        if not text:
            return ""
        # Replace multiple spaces with single space
        text = re.sub(r'[ \t]+', ' ', text)
        # Replace 3 or more newlines with double newline
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        # Strip leading and trailing whitespace
        return text.strip()
