# utils/qdrant_client.py

from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct,
    VectorParams,
    Distance,
    OptimizersConfigDiff,
    Filter,
    FieldCondition,
    MatchValue
)
import uuid
import os

qdrant = QdrantClient(url=os.getenv("QDRANT_URL", "http://qdrant:6333"))
COLLECTION = "immigration_docs"


def setup_collection():
    existing = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION not in existing:
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            optimizers_config=OptimizersConfigDiff(indexing_threshold=20000)
        )
        print(f"✅ Created Qdrant collection: {COLLECTION}")
    else:
        print(f"✅ Collection '{COLLECTION}' already exists")


def delete_chunks_by_url(source_url: str):
    """Delete all existing vectors for a given source URL before reinserting."""
    result = qdrant.delete(
        collection_name=COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="source_url",
                    match=MatchValue(value=source_url)
                )
            ]
        )
    )
    print(f"  🗑️  Deleted old chunks for: {source_url}")
    return result


def upsert_chunks(chunks: list[dict], source_url: str = None):
    """
    If source_url is provided, delete all old chunks for that URL first
    to prevent stale/orphaned vectors from persisting after content updates.
    """
    if source_url:
        delete_chunks_by_url(source_url)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=chunk["vector"],
            payload={
                "text":         chunk["text"],
                "source_url":   chunk["source_url"],
                "topic":        chunk["topic"],
                "scraped_date": chunk["scraped_date"]
            }
        )
        for chunk in chunks
    ]

    for i in range(0, len(points), 100):
        qdrant.upsert(
            collection_name=COLLECTION,
            points=points[i:i + 100]
        )

    print(f"  ↳ Upserted {len(points)} chunks into Qdrant")