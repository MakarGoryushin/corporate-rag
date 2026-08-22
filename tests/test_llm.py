from app.llm import OllamaLLM


def test_llm():
    llm = OllamaLLM()

    answer = llm.generate(
        "Ответь одним предложением: какая столица России?"
    )

    print("\nОтвет LLM:")
    print(answer)

    assert answer
    assert "Москва" in answer