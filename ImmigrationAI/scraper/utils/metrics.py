import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prom_multiproc")
os.makedirs(os.environ["PROMETHEUS_MULTIPROC_DIR"], exist_ok=True)

from prometheus_client import Counter, Histogram

PAGES_INGESTED = Counter(
    "pages_ingested_total",
    "Pages successfully embedded into Qdrant",
    ["topic"]
)

PAGES_SKIPPED = Counter(
    "pages_skipped_total",
    "Pages skipped due to unchanged content hash",
    ["topic"]
)

PAGES_FAILED = Counter(
    "pages_failed_total",
    "Pages that failed during ingestion",
    ["topic"]
)

EMBED_DURATION = Histogram(
    "embed_duration_seconds",
    "Time spent embedding a page's text",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

DB_WRITE_DURATION = Histogram(
    "db_write_duration_seconds",
    "Time spent writing hash to Postgres",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
)

QDRANT_UPSERT_DURATION = Histogram(
    "qdrant_upsert_duration_seconds",
    "Time spent upserting vectors into Qdrant",
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)