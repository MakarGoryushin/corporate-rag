from app.embeddings import EmbeddingModel
from app.qdrant import QdrantStorage


def test_embedding_and_search():
    embedding_model = EmbeddingModel()

    storage = QdrantStorage(
        vector_size=embedding_model.dimension
    )

    documents = [
        "Москва является столицей России.",
        "Париж является столицей Франции.",
        "Берлин является столицей Германии.",
    ]

    for document_id, text in enumerate(documents, start=1):
        vector = embedding_model.encode(text)

        storage.add_document(
            document_id=document_id,
            text=text,
            vector=vector,
        )

    query = "Какая столица у России?"

    query_vector = embedding_model.encode(query)

    results = storage.search(
        vector=query_vector,
        limit=3,
    )

    assert len(results) > 0

    print("\nРезультаты поиска:")

    for result in results:
        print(
            f"score={result.score:.4f} "
            f"text={result.payload['text']}"
        )

    assert "Москва" in results[0].payload["text"]