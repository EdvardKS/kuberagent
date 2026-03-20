import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from config.settings import (
    PICASSO_URL,
    CHAT_MODEL,
    EMBED_MODEL,
    VISION_MODEL,
    REDIS_URL,
    VECTOR_DB_URL,
)


class VectorStore:
    def __init__(self):
        self.url = VECTOR_DB_URL
        self.collection = "documents"

        self.client = QdrantClient(url=self.url)

        self._initialized = False
        self._dim = None

    def _normalize(self, embedding):
        if isinstance(embedding, dict):
            embedding = embedding.get("embedding", [])
        return embedding

    def _ensure_collection(self, dim):
        if self._initialized:
            return

        collections = self.client.get_collections().collections
        names = [c.name for c in collections]

        if self.collection not in names:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=dim,
                    distance=Distance.COSINE,
                ),
            )
        else:
            # Validar dimensión existente
            info = self.client.get_collection(self.collection)
            existing_dim = info.config.params.vectors.size  # type: ignore

            if existing_dim != dim:
                raise ValueError(
                    f"Dimensión incompatible: colección={existing_dim}, embedding={dim}"
                )

        self._initialized = True
        self._dim = dim

    def add(self, embedding, text):
        vec = self._normalize(embedding)

        dim = len(vec)
        print(f"[VectorStore] inicializado con dim={dim}")
        # 🔴 inicialización segura
        self._ensure_collection(dim)

        point_id = abs(hash(text)) % (10**12)

        self.client.upsert(
            collection_name=self.collection,
            points=[
                {
                    "id": point_id,
                    "vector": vec,
                    "payload": {"text": text},
                }  # type: ignore
            ],
        )


    def search(self, embedding, k=3):
        vec = self._normalize(embedding)

        results = self.client.query_points(
            collection_name=self.collection,
            query=vec,
            limit=k,
        )

        print("RESULTS RAW:", results)

        texts = [point.payload.get("text", "") for point in results.points]

        print("TEXTS:", texts)

        return texts
    
 

vector_store = VectorStore()
