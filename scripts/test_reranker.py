from app.retriever import Retriever
from app.reranker import Reranker


query = "Сколько дней ежегодного отпуска предоставляется сотруднику?"

retrieved = Retriever().retrieve(
    query,
    limit=10,
)

print("=== ДО RERANK ===")

for doc in retrieved:
    print(
        f"{doc['score']:.4f}",
        doc["source"],
    )

reranker = Reranker()

reranked = reranker.rerank(
    query,
    retrieved,
)

print()
print("=== ПОСЛЕ RERANK ===")

for doc in reranked:
    print(
        f"{doc['rerank_score']:.4f}",
        doc["source"],
    )