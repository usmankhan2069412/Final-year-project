import re
from typing import List
from app.core.config import settings

class TextChunker:
    @staticmethod
    def split_text(text: str, chunk_size: int = settings.CHUNK_SIZE, overlap: int = settings.CHUNK_OVERLAP) -> List[str]:
        if not text.strip():
            return []

        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if overlap < 0:
            raise ValueError("overlap cannot be negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        normalized = re.sub(r"\s+", " ", text).strip()
        if len(normalized) <= chunk_size:
            return [normalized]

        chunks = []
        start = 0
        text_len = len(normalized)

        while start < text_len:
            target_end = min(start + chunk_size, text_len)
            end = target_end

            if target_end < text_len:
                boundary_window_start = max(start + int(chunk_size * 0.5), start)
                sentence_boundaries = [
                    normalized.rfind(". ", boundary_window_start, target_end),
                    normalized.rfind("? ", boundary_window_start, target_end),
                    normalized.rfind("! ", boundary_window_start, target_end),
                    normalized.rfind("; ", boundary_window_start, target_end),
                    normalized.rfind(", ", boundary_window_start, target_end),
                ]
                best_boundary = max(sentence_boundaries)
                if best_boundary <= start:
                    best_boundary = normalized.rfind(" ", boundary_window_start, target_end)
                if best_boundary > start:
                    end = best_boundary + 1

            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= text_len:
                break

            start = max(end - overlap, start + 1)

        return chunks
