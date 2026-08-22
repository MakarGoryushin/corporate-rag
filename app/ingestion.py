import re
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import uuid
from app.chunker import TextChunker
from app.embeddings import EmbeddingModel
from app.loaders import DocumentLoader
from app.qdrant import QdrantStorage

INDEX_VERSION = 3

class DocumentIngestion:
    def __init__(self, embedding_model=None, storage=None, chunker=None, loader=None):
        self.embedding_model = embedding_model or EmbeddingModel()
        self.storage = storage or QdrantStorage(vector_size=self.embedding_model.dimension)
        self.chunker = chunker or TextChunker()
        self.loader = loader or DocumentLoader()

    def ingest(self, file_path: str) -> int:
        result = self.ingest_with_status(file_path)
        return result["chunks"]

    def ingest_with_status(
            self,
            file_path: str,
    ) -> dict:
        path = Path(file_path).resolve()
        raw = path.read_bytes()

        document_id = hashlib.sha256(
            str(path).encode("utf-8")
        ).hexdigest()

        content_hash = hashlib.sha256(raw).hexdigest()

        existing_document = self.storage.find_document(
            document_id
        )

        duplicate = self.storage.find_by_content_hash(
            content_hash
        )

        existing_is_current = (
                existing_document
                and existing_document.get("index_version")
                == INDEX_VERSION
        )

        if (
                duplicate
                and duplicate.get("index_version")
                == INDEX_VERSION
                and (
                not existing_document
                or existing_is_current
        )
        ):
            return {
                "status": "duplicate",
                "chunks": 0,
                "document_id": duplicate.get(
                    "document_id"
                ),
                "existing_source": duplicate.get(
                    "source"
                ),
            }

        text = self.loader.load(str(path))
        chunks = self.chunker.split(text)

        document_header = " ".join(
            text[:1200].split()
        )

        author_match = re.search(
            r"Выполнил\s+студент\s+([^\r\n]+)",
            text,
            flags=re.IGNORECASE,
        )

        author = None

        if author_match:
            author = author_match.group(1).strip()
            author = re.sub(
                r"\s{2,}.*$",
                "",
                author,
            ).strip()

        texts_for_embedding = []

        for chunk in chunks:
            if author:
                embedding_text = (
                    f"Практику выполнил студент: "
                    f"{author}.\n"
                    f"Фрагмент документа: {chunk}"
                )
            else:
                embedding_text = chunk

            texts_for_embedding.append(
                embedding_text
            )

        vectors = (
            self.embedding_model.encode_many(
                texts_for_embedding
            )
            if texts_for_embedding
            else []
        )

        now = datetime.now(timezone.utc).isoformat()
        points = []

        for index, (chunk, vector) in enumerate(
                zip(chunks, vectors)
        ):
            point_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{document_id}:{index}",
                )
            )

            points.append(
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": {
                        "text": chunk,
                        "author": author,
                        "document_id": document_id,
                        "content_hash": content_hash,
                        "source": str(path),
                        "file_name": path.name,
                        "extension": path.suffix.lower(),
                        "chunk_index": index,
                        "indexed_at": now,
                        "index_version": INDEX_VERSION,
                    },
                }
            )

        self.storage.replace_document(
            document_id,
            points,
        )

        return {
            "status": (
                "updated"
                if existing_document
                else "indexed"
            ),
            "chunks": len(points),
            "document_id": document_id,
            "existing_source": None,
        }

    def ingest_directory(self, directory: str, recursive: bool = True) -> dict:
        root = Path(directory)
        if not root.exists(): raise FileNotFoundError(f"Директория не найдена: {root}")
        if not root.is_dir(): raise ValueError(f"Это не директория: {root}")
        iterator = root.rglob("*") if recursive else root.glob("*")
        files = sorted(p for p in iterator if p.is_file() and p.suffix.lower() in self.loader.supported_extensions)
        result = {"documents": 0, "chunks": 0, "errors": []}
        for path in files:
            try:
                result["chunks"] += self.ingest(str(path)); result["documents"] += 1
            except Exception as exc:
                result["errors"].append({"file": str(path), "error": str(exc)})
        return result
