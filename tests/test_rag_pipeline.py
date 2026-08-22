from app.rag import RAGPipeline


def test_rag_pipeline():
    rag = RAGPipeline()

    result = rag.answer(
        "Какая столица России?",
        limit=3,
    )

    print("\nОтвет RAG:")
    print(result["answer"])

    print("\nИсточники:")
    for source in result["sources"]:
        print(
            f"score={source['score']:.4f} "
            f"text={source['text']}"
        )

    assert result["answer"]
    assert result["sources"]
    assert "Москва" in result["answer"]