import os
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
BATCH_SIZE = 500


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Embed chunks in batches of 500 to stay under OpenAI's 2048 input limit."""
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c["text"] for c in batch]

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )

        for j, embedding_obj in enumerate(response.data):
            chunks[i + j]["vector"] = embedding_obj.embedding

        print(f"  🔢 Embedded batch {i // BATCH_SIZE + 1} ({len(batch)} chunks)")

    return chunks