from app.rag import RAGPipeline


def main():
    rag = RAGPipeline()

    questions = [
        "Сколько дней ежегодного отпуска предоставляется сотруднику?",
        "За сколько дней нужно подать заявление на отпуск?",
        "Какие требования предъявляются к корпоративным паролям?",
        "Где находится головной офис компании Альфа?",
    ]

    for question in questions:
        print("=" * 80)
        print(f"ВОПРОС: {question}")
        print()

        result = rag.answer(
            question,
            limit=5,
        )

        print(f"ОТВЕТ: {result['answer']}")
        print()

        print("ИСТОЧНИКИ:")

        for source in result["sources"]:
            print(
                f"- score={source['score']:.4f}, "
                f"source={source['source']}, "
                f"chunk={source['chunk_index']}"
            )

        print()


if __name__ == "__main__":
    main()