from app.retriever import Retriever


def test_vacation_retrieval():
    retriever = Retriever()

    results = retriever.retrieve(
        "Сколько дней ежегодного отпуска предоставляется сотруднику?",
        limit=5,
    )

    assert results
    assert results[0]["source"] == r"data\raw\hr.txt"


def test_vacation_application_retrieval():
    retriever = Retriever()

    results = retriever.retrieve(
        "За сколько дней нужно подать заявление на отпуск?",
        limit=5,
    )

    assert results
    assert results[0]["source"] == r"data\raw\hr.txt"


def test_password_retrieval():
    retriever = Retriever()

    results = retriever.retrieve(
        "Какие требования предъявляются к корпоративным паролям?",
        limit=5,
    )

    assert results
    assert results[0]["source"] == r"data\raw\security.txt"


def test_office_retrieval():
    retriever = Retriever()

    results = retriever.retrieve(
        "Где находится головной офис компании Альфа?",
        limit=5,
    )

    assert results
    assert results[0]["source"] == r"data\raw\company.txt"