# scraper/pipeline.py
import logging
import hashlib
import json
from datetime import datetime, timezone
import sys

from utils.metrics import (
    PAGES_INGESTED, PAGES_SKIPPED, PAGES_FAILED,
    EMBED_DURATION, DB_WRITE_DURATION, QDRANT_UPSERT_DURATION,
)
from utils.db import hash_exists, upsert_hash
from utils.chunker import chunk_text
from utils.embedder import embed_chunks
from utils.qdrant_client import upsert_chunks


logging.basicConfig(
    stream=sys.stdout,      # ← stdout instead of a file
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger("immigrationiq.pipeline")


def _log(event: str, **kwargs):
    logger.info(json.dumps({"event": event, **kwargs}))


def ingest_page(url: str, raw_text: str, topic: str):
    page_hash = hashlib.sha256(raw_text.encode()).hexdigest()

    try:
        # ── Skip unchanged pages ────────────
        if hash_exists(url, page_hash):
            PAGES_SKIPPED.labels(topic=topic).inc()
            _log("page_skipped", url=url, topic=topic, reason="unchanged_hash")
            return

        scraped_date = datetime.now(timezone.utc).isoformat()

        # ── Chunk ───────────────────────────
        chunks = chunk_text(raw_text, url=url, topic=topic, scraped_date=scraped_date)

        if not chunks:
            _log("page_skipped", url=url, topic=topic, reason="no_chunks")
            return

        # ── Embed ───────────────────────────
        with EMBED_DURATION.time():
            chunks = embed_chunks(chunks)

        # ── Upsert to Qdrant ────────────────
        with QDRANT_UPSERT_DURATION.time():
            upsert_chunks(chunks, source_url=url)

        # ── Write hash to Postgres ──────────
        with DB_WRITE_DURATION.time():
            upsert_hash(url, page_hash, topic)

        PAGES_INGESTED.labels(topic=topic).inc()
        _log("page_ingested", url=url, topic=topic,
             chunks=len(chunks), text_length=len(raw_text))

    except Exception as e:
        PAGES_FAILED.labels(topic=topic).inc()
        _log("page_failed", url=url, topic=topic, error=str(e))
        raise