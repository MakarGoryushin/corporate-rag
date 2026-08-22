from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_BATCH_SIZE, EMBEDDING_MODEL

class EmbeddingModel:
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model = SentenceTransformer(model_name, device="cpu")

    def encode(self, text: str, *, is_query: bool = False) -> list[float]:
        return self.encode_many([text], is_query=is_query)[0]

    def encode_many(self, texts: list[str], *, is_query: bool = False) -> list[list[float]]:
        prefix = "query: " if is_query else "passage: "
        vectors = self.model.encode(
            [prefix + text for text in texts], batch_size=EMBEDDING_BATCH_SIZE,
            normalize_embeddings=True, show_progress_bar=len(texts) > EMBEDDING_BATCH_SIZE,
        )
        return vectors.tolist()

    @property
    def dimension(self) -> int:
        return int(self.model.get_sentence_embedding_dimension())
