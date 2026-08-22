from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams
from app.config import QDRANT_COLLECTION, QDRANT_HOST, QDRANT_PORT

class QdrantStorage:
    def __init__(self, host=QDRANT_HOST, port=QDRANT_PORT, collection_name=QDRANT_COLLECTION,
                 vector_size: int = 384, client: QdrantClient | None = None):
        self.client = client or QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.vector_size = vector_size
        self._create_collection()

    def _create_collection(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE))

    def replace_document(self, document_id: str, points: list[dict]):
        self.client.delete(self.collection_name,
            points_selector=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]))
        if points:
            self.client.upsert(self.collection_name, points=[PointStruct(**point) for point in points], wait=True)

    def _find_payload(
        self,
        field_name: str,
        value: str,
    ) -> dict | None:
        records, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key=field_name,
                        match=MatchValue(value=value),
                    )
                ]
            ),
            limit=1,
            with_payload=True,
            with_vectors=False,
        )

        if not records:
            return None

        return records[0].payload or {}

    def find_document(
        self,
        document_id: str,
    ) -> dict | None:
        return self._find_payload(
            "document_id",
            document_id,
        )

    def delete_document(
        self,
        document_id: str,
    ) -> dict | None:
        document = self.find_document(
            document_id
        )

        if not document:
            return None

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(
                            value=document_id
                        ),
                    )
                ]
            ),
            wait=True,
        )

        return document

    def find_by_content_hash(
        self,
        content_hash: str,
    ) -> dict | None:
        return self._find_payload(
            "content_hash",
            content_hash,
        )

    def add_document(self, document_id, text, vector, metadata=None):
        payload = {"text": text, **(metadata or {})}
        self.client.upsert(self.collection_name, points=[PointStruct(id=document_id, vector=vector, payload=payload)], wait=True)

    def search(self, vector: list[float], limit: int = 5):
        return self.client.query_points(self.collection_name, query=vector, limit=limit).points

    def list_documents(self) -> list[dict]:
        documents = {}
        offset = None

        while True:
            records, offset = self.client.scroll(
                collection_name=self.collection_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            for record in records:
                payload = record.payload or {}
                document_id = payload.get("document_id")

                if not document_id:
                    continue

                if document_id not in documents:
                    documents[document_id] = {
                        "document_id": document_id,
                        "file_name": payload.get(
                            "file_name"
                        ),
                        "extension": payload.get(
                            "extension"
                        ),
                        "source": payload.get("source"),
                        "content_hash": payload.get(
                            "content_hash"
                        ),
                        "indexed_at": payload.get(
                            "indexed_at"
                        ),
                        "chunks": 0,
                    }

                documents[document_id]["chunks"] += 1

            if offset is None:
                break

        return sorted(
            documents.values(),
            key=lambda document: (
                document.get("file_name") or ""
            ).lower(),
        )

    def clear(self, vector_size: int | None = None):
        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)
        self.vector_size = vector_size or self.vector_size
        self._create_collection()

    def get_collection_info(self):
        return self.client.get_collection(self.collection_name)
