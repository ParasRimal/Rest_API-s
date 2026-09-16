import uuid
from pathlib import Path
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Local persistent storage path aligned with target directory structure
STORAGE_PATH = Path("storage/qdrant_storage")
STORAGE_PATH.mkdir(parents=True, exist_ok=True)

class QdrantService:
    def __init__(self):
        # Uses local disk storage to persist embeddings across server restarts without network timeouts
        self.client = QdrantClient(path=str(STORAGE_PATH))

    def ensure_collection(self, collection_name: str, vector_size: int = 384):
        try:
            collections = [col.name for col in self.client.get_collections().collections]
            if collection_name not in collections:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
        except Exception as e:
            print(f"[Vector DB Collection Error]: {e}")

    def store_embeddings(
        self,
        collection_name: str,
        chunks: List[str],
        embeddings: List[List[float]],
        document_id: str,
        filename: str
    ):
        if not embeddings:
            return
            
        self.ensure_collection(collection_name, vector_size=len(embeddings[0]))

        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            payload: Dict[str, Any] = {
                "document_id": document_id,
                "chunk_index": i,
                "text": chunk,
                "filename": filename
            }
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload=payload
            )
            points.append(point)

        self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    def search_similar(self, collection_name: str, query_vector: List[float], top_k: int = 3) -> List[str]:
        extracted_texts = []
        try:
            # Universal fetch compatible across qdrant-client versions
            if hasattr(self.client, "query_points"):
                res = self.client.query_points(
                    collection_name=collection_name,
                    query=query_vector,
                    limit=top_k
                )
                hits = res.points if hasattr(res, "points") else res
            else:
                hits = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=top_k
                )

            for hit in hits:
                if hasattr(hit, "payload") and hit.payload and "text" in hit.payload:
                    extracted_texts.append(hit.payload["text"])
        except Exception as e:
            print(f"[Vector DB Search Error]: {e}")
            
        return extracted_texts

vector_db_service = QdrantService()