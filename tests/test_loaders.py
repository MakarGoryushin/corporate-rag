from app.loaders import DocumentLoader


def test_load_txt():
    loader = DocumentLoader()

    text = loader.load("data/raw/document.txt")

    assert "Москва" in text
    assert "Россия" in text

    print("\nЗагруженный текст:")
    print(text)