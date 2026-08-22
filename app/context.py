class ContextBuilder:
    def build(
        self,
        query: str,
        results: list[dict],
    ) -> str:
        if not results:
            return (
                "Контекст не найден.\n\n"
                f"Вопрос: {query}"
            )

        groups = {}

        for index, result in enumerate(
            results,
            start=1,
        ):
            author = result.get("author")
            group_key = author or "Без указанного автора"

            groups.setdefault(
                group_key,
                [],
            ).append(
                (index, result)
            )

        context_groups = []

        for author, group_results in groups.items():
            group_parts = [
                "================================",
                f"ГРУППА ДОКУМЕНТА: {author}",
                (
                    "Все фрагменты внутри этой группы "
                    f"относятся только к: {author}."
                ),
            ]

            for source_number, result in group_results:
                file_name = result.get(
                    "file_name",
                    "Неизвестный документ",
                )
                text = result["text"]

                group_parts.append(
                    (
                        f"\n[Источник {source_number}]\n"
                        f"Автор: {author}\n"
                        f"Документ: {file_name}\n"
                        f"Фрагмент:\n{text}"
                    )
                )

            group_parts.append(
                f"КОНЕЦ ГРУППЫ: {author}"
            )

            context_groups.append(
                "\n".join(group_parts)
            )

        context = "\n\n".join(context_groups)

        return (
            "Контекст разделён на независимые группы.\n"
            "Запрещено переносить факты, задачи и результаты "
            "из одной группы в другую.\n"
            "При ответе по человеку используй только фрагменты "
            "внутри группы этого человека.\n\n"
            f"{context}\n\n"
            f"ВОПРОС:\n{query}"
        )