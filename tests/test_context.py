from app.context import ContextBuilder


def test_context_builder():
    builder = ContextBuilder()

    results = [
        {
            "score": 0.91,
            "text": "Москва является столицей России.",
            "source": "data/raw/document.txt",
            "file_name": "document.txt",
            "document_id": "document-1",
            "chunk_index": 0,
        },
        {
            "score": 0.75,
            "text": "Россия находится в Европе и Азии.",
            "source": "data/raw/document.txt",
            "file_name": "document.txt",
            "document_id": "document-1",
            "chunk_index": 1,
        },
    ]

    context = builder.build(
        query="Какая столица России?",
        results=results,
    )

    assert "Какая столица России?" in context
    assert "Москва является столицей России." in context
    assert "Россия находится в Европе и Азии." in context

    assert "[Источник 1]" in context
    assert "[Источник 2]" in context
    assert "Документ: document.txt" in context

    assert "data/raw/document.txt" not in context