import re

from app.config import (
    ENABLE_RERANKER,
    MAX_CHUNKS_PER_DOCUMENT,
    RELATIVE_SCORE_MARGIN,
    RERANK_SCORE_THRESHOLD,
    RETRIEVAL_INITIAL_LIMIT,
    RETRIEVAL_LIMIT,
)

from app.context import ContextBuilder
from app.llm import OpenAICompatibleLLM
from app.retriever import Retriever


NO_ANSWER = (
    "В предоставленных документах нет информации "
    "для ответа."
)


class RAGPipeline:
    def __init__(
        self,
        retriever=None,
        context_builder=None,
        llm=None,
        reranker=None,
    ):
        self.retriever = retriever or Retriever()
        self.context_builder = (
            context_builder or ContextBuilder()
        )
        self.llm = llm or OpenAICompatibleLLM()

        if reranker is not None:
            self.reranker = reranker
        elif ENABLE_RERANKER:
            from app.reranker import Reranker

            self.reranker = Reranker()
        else:
            self.reranker = None

    @staticmethod
    def _looks_like_table_of_contents(
        result: dict,
    ) -> bool:
        text = result.get("text", "")
        normalized = text.lower()

        if "содержание" not in normalized:
            return False

        numbered_headings = re.findall(
            r"\b\d+(?:\.\d+)+\s+\S+",
            text,
        )

        return len(numbered_headings) >= 4

    @classmethod
    def _remove_table_of_contents(
        cls,
        results: list[dict],
    ) -> list[dict]:
        return [
            result
            for result in results
            if not cls._looks_like_table_of_contents(
                result
            )
        ]

    @staticmethod
    def _diversify_by_document(
        results: list[dict],
        max_chunks_per_document: int,
    ) -> list[dict]:
        selected = []
        document_counts = {}

        for result in results:
            document_key = (
                result.get("document_id")
                or result.get("source")
                or result.get("file_name")
                or "unknown"
            )

            current_count = document_counts.get(
                document_key,
                0,
            )

            if current_count >= max_chunks_per_document:
                continue

            selected.append(result)
            document_counts[document_key] = (
                current_count + 1
            )

        return selected

    @staticmethod
    def _filter_by_relative_score(
        results: list[dict],
        margin: float,
    ) -> list[dict]:
        if not results:
            return []

        best_score = results[0]["score"]
        minimum_score = best_score - margin

        return [
            result
            for result in results
            if result["score"] >= minimum_score
        ]

    def answer(
        self,
        query: str,
        limit: int = RETRIEVAL_LIMIT,
        initial_limit: int = RETRIEVAL_INITIAL_LIMIT,
    ) -> dict:
        results = self.retriever.retrieve(
            query,
            limit=max(limit, initial_limit),
        )

        results = self._remove_table_of_contents(
            results
        )

        if self.reranker:
            results = self.reranker.rerank(
                query,
                results,
            )

            results = [
                result
                for result in results
                if result.get(
                    "rerank_score",
                    float("-inf"),
                ) >= RERANK_SCORE_THRESHOLD
            ]
        else:
            results = self._filter_by_relative_score(
                results,
                RELATIVE_SCORE_MARGIN,
            )

        results = self._diversify_by_document(
            results,
            MAX_CHUNKS_PER_DOCUMENT,
        )

        results = results[:limit]

        context = self.context_builder.build(
            query,
            results,
        )

        if not results:
            answer = NO_ANSWER

        elif not self.llm.configured:
            answer = (
                "LLM не настроена. Ниже возвращены "
                "найденные фрагменты источников."
            )

        else:
            prompt = (
                "Ты — корпоративный ассистент.\n"
                "Ответь на вопрос, используя исключительно "
                "предоставленный контекст.\n\n"
                "Правила:\n"
                "1. Не используй знания, которых нет "
                "в контексте.\n"
                "2. Не изменяй числа, имена, сроки "
                "и условия.\n"
                "3. Не додумывай отсутствующие факты.\n"
                "4. После каждого утверждения указывай "
                "ссылку только в формате [Источник N].\n"
                "5. Если информации недостаточно, ответь "
                f"только фразой: \"{NO_ANSWER}\"\n"
                "6. Дай полный, но лаконичный ответ "
                "по-русски.\n"
                "7. Используй относящиеся к вопросу сведения "
                "из всех предоставленных источников.\n"
                "8. Не ограничивайся первым источником, "
                "если другие источники дополняют ответ.\n"
                "9. Не повторяй одинаковые факты "
                "и пункты списка.\n"
                "10. Если сведения относятся к разным людям "
                "или документам, явно разделяй их.\n"
                                "11. Задачи из каждого источника приписывай "
                "только автору, указанному возле этого "
                "источника.\n"
                "12. Не используй оглавление как доказательство "
                "выполнения задачи, если найденный фрагмент "
                "этого не подтверждает.\n"
                "13. Не копируй пути к файлам, оценки "
                "релевантности и номера чанков.\n"
                f"{context}\n\n"
                "ОТВЕТ:"
            )

            answer = self.llm.generate(prompt)

            normalized_answer = (
                answer.lower().replace("ё", "е")
            )

            no_answer_markers = (
                "нет информации для ответа",
                "информации недостаточно",
                "информация отсутствует",
                "не найдено информации",
            )

            if any(
                marker in normalized_answer
                for marker in no_answer_markers
            ):
                answer = NO_ANSWER
                results = []
            else:
                citations = ", ".join(
                    f"[Источник {index}]"
                    for index in range(
                        1,
                        len(results) + 1,
                    )
                )

                answer = (
                    f"{answer.rstrip()}\n\n"
                    f"Использованные источники: "
                    f"{citations}."
                )
        return {
            "answer": answer,
            "sources": results,
            "context": context,
        }