from app.retriever import Retriever


def test_retriever():
    retriever = Retriever()

    results = retriever.retrieve(
        "Какая столица России?",
        limit=3,
    )

    print("\nРезультаты retrieval:")

    for result in results:
        print(
            f"score={result['score']:.4f} "
            f"text={result['text']}"
        )

    assert len(results) > 0

    assert any(
        "Москва" in result["text"]
        for result in results
    )