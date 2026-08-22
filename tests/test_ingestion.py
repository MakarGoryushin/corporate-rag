from app.ingestion import DocumentIngestion


def test_ingestion():
    ingestion = DocumentIngestion()

    chunks_count = ingestion.ingest(
        "data/raw/document.txt"
    )

    print(f"\nЗагружено chunks: {chunks_count}")

    assert chunks_count > 0