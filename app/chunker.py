import re
from app.config import CHUNK_OVERLAP, CHUNK_SIZE

class TextChunker:
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        if chunk_size <= 0:
            raise ValueError("chunk_size должен быть больше 0")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap должен быть от 0 до chunk_size - 1")
        self.chunk_size, self.chunk_overlap = chunk_size, chunk_overlap

    @staticmethod
    def normalize(text: str) -> str:
        text = text.replace("\u00a0", " ").replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        return re.sub(r"\n{3,}", "\n\n", text).strip()

    def split(self, text: str) -> list[str]:
        text = self.normalize(text)
        if not text:
            return []
        units = [p.strip() for p in re.split(r"(?<=[.!?…])\s+|\n+", text) if p.strip()]
        pieces = [piece for unit in units for piece in self._split_oversized(unit)]
        chunks, current = [], []
        for piece in pieces:
            candidate = " ".join(current + [piece])
            if current and len(candidate) > self.chunk_size:
                chunk = " ".join(current)
                chunks.append(chunk)
                overlap_words, overlap_length = [], 0
                for word in reversed(chunk.split()):
                    extra = len(word) + (1 if overlap_words else 0)
                    if overlap_length + extra > self.chunk_overlap:
                        break
                    overlap_words.insert(0, word)
                    overlap_length += extra
                overlap = " ".join(overlap_words)
                current = ([overlap] if overlap else []) + [piece]
                while len(" ".join(current)) > self.chunk_size and len(current) > 1:
                    current.pop(0)
            else:
                current.append(piece)
        if current:
            chunks.append(" ".join(current))
        return [chunk for chunk in chunks if chunk]

    def _split_oversized(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]
        result, current = [], ""
        for word in text.split():
            if len(word) > self.chunk_size:
                if current:
                    result.append(current); current = ""
                result.extend(word[i:i+self.chunk_size] for i in range(0, len(word), self.chunk_size))
                continue
            candidate = f"{current} {word}".strip()
            if current and len(candidate) > self.chunk_size:
                result.append(current); current = word
            else:
                current = candidate
        if current:
            result.append(current)
        return result
