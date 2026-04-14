import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()


def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def setup_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scraped_pages (
                    id          SERIAL PRIMARY KEY,
                    url         TEXT UNIQUE NOT NULL,
                    content_hash TEXT NOT NULL,
                    scraped_at  TIMESTAMP DEFAULT NOW(),
                    topic       TEXT
                );
            """)
        conn.commit()
    print("✅ Database ready")


def hash_exists(url: str, new_hash: str) -> bool:
    """Returns True if URL was already scraped with the same content hash."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT content_hash FROM scraped_pages WHERE url = %s", (url,)
            )
            row = cur.fetchone()
            return row is not None and row[0] == new_hash


def upsert_hash(url: str, content_hash: str, topic: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO scraped_pages (url, content_hash, topic)
                VALUES (%s, %s, %s)
                ON CONFLICT (url) DO UPDATE
                SET content_hash = EXCLUDED.content_hash,
                    scraped_at   = NOW();
            """, (url, content_hash, topic))
        conn.commit()