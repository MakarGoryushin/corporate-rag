from app.chunker import TextChunker


def test_chunking():
    text = (
        "Это первое предложение. "
        "Это второе предложение. "
        "Это третье предложение. "
        "Это четвертое предложение. "
        "Это пятое предложение."
    )

    chunker = TextChunker(
        chunk_size=50,
        chunk_overlap=10,
    )

    chunks = chunker.split(text)

    assert len(chunks) > 1

    assert all(len(chunk) <= 50 for chunk in chunks)

    for chunk in chunks:
        assert not chunk.startswith("ожение")
        assert not chunk.endswith("Эт")

    print("\nChunks:")

    for index, chunk in enumerate(chunks):
        print(f"{index}: {chunk}")