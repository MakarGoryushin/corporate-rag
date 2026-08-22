from app.config import RETRIEVAL_LIMIT, SCORE_THRESHOLD
from app.embeddings import EmbeddingModel
from app.qdrant import QdrantStorage

class Retriever:
    def __init__(self, embedding_model=None, storage=None):
        self.embedding_model = embedding_model or EmbeddingModel()
        self.storage = storage or QdrantStorage(vector_size=self.embedding_model.dimension)

    def retrieve(self, query: str, limit=RETRIEVAL_LIMIT, score_threshold=SCORE_THRESHOLD) -> list[dict]:
        if not query.strip(): raise ValueError("Запрос не должен быть пустым")
        points = self.storage.search(self.embedding_model.encode(query, is_query=True), limit=limit)
        results = []
        for point in points:
            payload = point.payload or {}
            if point.score >= score_threshold and payload.get("text"):
                results.append({"score": float(point.score), **payload})
        return results
