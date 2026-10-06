import os
import re
from typing import List, Dict, Any, Tuple
from services.pdf_processor import PDFProcessor

class DocumentProcessor:
    """
    Coordinates multi-format document text extraction, cleaning, chunking,
    and grounded retrieval search.
    """

    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}
    DEFAULT_CHUNK_SIZE = 750
    DEFAULT_CHUNK_OVERLAP = 120

    @classmethod
    def allowed_file(cls, filename: str) -> bool:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in cls.ALLOWED_EXTENSIONS

    @classmethod
    def process_file(cls, file_path: str, filename: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        Extracts content from PDF, TXT, or DOCX.
        Returns:
            chunks: List of {'page_number': int, 'chunk_text': str, 'chunk_index': int}
            total_pages: int
        """
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        pages_data = []
        total_pages = 1

        if ext == 'pdf':
            pages_data = PDFProcessor.extract_text_by_pages(file_path)
            total_pages = max(len(pages_data), 1)
        elif ext == 'txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            cleaned = PDFProcessor.clean_text(content)
            pages_data = [{'page_number': 1, 'text': cleaned}]
            total_pages = 1
        elif ext == 'docx':
            try:
                import docx
                doc = docx.Document(file_path)
                full_text = []
                for para in doc.paragraphs:
                    if para.text.strip():
                        full_text.append(para.text.strip())
                content = "\n\n".join(full_text)
                cleaned = PDFProcessor.clean_text(content)
                pages_data = [{'page_number': 1, 'text': cleaned}]
                total_pages = 1
            except Exception as e:
                print(f"DOCX extraction fallback: {e}")
                pages_data = [{'page_number': 1, 'text': ''}]
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        # Split extracted pages into chunks
        chunks = []
        chunk_idx = 0
        for page in pages_data:
            page_num = page['page_number']
            page_text = page['text']
            
            # If text is small, treat as single chunk
            if len(page_text) <= cls.DEFAULT_CHUNK_SIZE:
                if page_text.strip():
                    chunks.append({
                        'page_number': page_num,
                        'chunk_text': page_text.strip(),
                        'chunk_index': chunk_idx
                    })
                    chunk_idx += 1
                continue

            # Otherwise chunk with overlap
            words = page_text.split()
            current_chunk = []
            current_len = 0

            for word in words:
                current_chunk.append(word)
                current_len += len(word) + 1

                if current_len >= cls.DEFAULT_CHUNK_SIZE:
                    chunk_str = " ".join(current_chunk)
                    chunks.append({
                        'page_number': page_num,
                        'chunk_text': chunk_str,
                        'chunk_index': chunk_idx
                    })
                    chunk_idx += 1
                    # Overlap: keep last few words
                    overlap_words = current_chunk[-15:] if len(current_chunk) > 15 else []
                    current_chunk = list(overlap_words)
                    current_len = sum(len(w) + 1 for w in current_chunk)

            if current_chunk:
                chunk_str = " ".join(current_chunk).strip()
                if chunk_str:
                    chunks.append({
                        'page_number': page_num,
                        'chunk_text': chunk_str,
                        'chunk_index': chunk_idx
                    })
                    chunk_idx += 1

        return chunks, total_pages

    @staticmethod
    def search_relevant_chunks(chunks, query: str, top_k: int = 4) -> List[Any]:
        """
        Scores chunks based on keyword matching and relevance to the query.
        Returns top_k most relevant chunks.
        chunks can be a list of DocumentChunk model instances or dicts.
        """
        if not chunks or not query:
            return []

        # Tokenize and clean query
        query_words = set(re.findall(r'\b[a-zA-Z0-9_]{3,}\b', query.lower()))
        stop_words = {
            'what', 'when', 'where', 'which', 'who', 'whom', 'this', 'that', 'these',
            'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'do', 'does', 'did', 'the', 'and', 'but', 'if', 'or', 'because',
            'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
            'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
            'then', 'once', 'here', 'there', 'all', 'any', 'both', 'each', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now', 'explain',
            'tell', 'describe', 'give', 'define', 'meaning'
        }
        keywords = [w for w in query_words if w not in stop_words]
        if not keywords:
            keywords = list(query_words)

        scored = []
        for ch in chunks:
            text = ch.chunk_text if hasattr(ch, 'chunk_text') else ch.get('chunk_text', '')
            text_lower = text.lower()
            
            score = 0
            # Exact query phrase match boost
            if query.lower() in text_lower:
                score += 15.0

            # Keyword occurrence scoring
            for kw in keywords:
                count = text_lower.count(kw)
                if count > 0:
                    score += 2.0 + min(count, 5) * 0.5
                    # Heading/start of paragraph bonus
                    if kw in text_lower[:80]:
                        score += 3.0

            if score > 0:
                scored.append((score, ch))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [item[1] for item in scored[:top_k]]

        # If no keywords matched at all, return first few chunks as general context
        if not results:
            results = list(chunks[:top_k])

        return results
