from pathlib import Path
from app.chunker import TextChunker
from app.loaders import DocumentLoader

def test_empty_and_long_word_never_produce_empty_chunk():
    chunker = TextChunker(chunk_size=10, chunk_overlap=2)
    assert chunker.split("   ") == []
    chunks = chunker.split("а" * 25)
    assert chunks and all(chunks) and all(len(c) <= 10 for c in chunks)

def test_txt_cp1251(tmp_path: Path):
    path = tmp_path / "document.txt"
    path.write_bytes("Москва — столица".encode("cp1251"))
    assert "Москва" in DocumentLoader().load(str(path))

def test_unsupported_extension(tmp_path: Path):
    path = tmp_path / "file.csv"
    path.write_text("data", encoding="utf-8")
    try:
        DocumentLoader().load(str(path))
    except ValueError as exc:
        assert "Неподдерживаемый" in str(exc)
    else:
        raise AssertionError("ValueError expected")
