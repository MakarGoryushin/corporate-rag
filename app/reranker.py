from app.config import RERANKER_MODEL

class Reranker:
    def __init__(self, model_name=RERANKER_MODEL):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name, device="cpu")

    def rerank(self, query: str, documents: list[dict]) -> list[dict]:
        if not documents: return []
        scores = self.model.predict([(query, doc["text"]) for doc in documents])
        output = [dict(doc, rerank_score=float(score)) for doc, score in zip(documents, scores)]
        return sorted(output, key=lambda item: item["rerank_score"], reverse=True)
