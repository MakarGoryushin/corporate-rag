from app.rag import RAGPipeline

rag = RAGPipeline()

result = rag.answer(
    "Где находится головной офис компании Альфа?",
    limit=3,
)

print("\nОТВЕТ:")
print(result["answer"])

print("\nИСТОЧНИКИ:")

for source in result["sources"]:
    print(
        f"score={source['score']:.4f} "
        f"source={source['source']} "
        f"chunk={source['chunk_index']}"
    )