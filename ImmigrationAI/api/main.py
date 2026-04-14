import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI, OpenAIError
from qdrant_client import QdrantClient

# ── Init ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="ImmigrationIQ API",
    description="RAG-powered US immigration Q&A",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant = QdrantClient(url=os.getenv("QDRANT_URL", "http://qdrant:6333"))

COLLECTION      = "immigration_docs"
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL       = "gpt-4o-mini"
TOP_K           = 8
SCORE_THRESHOLD = 0.40   # minimum similarity — lowered to catch adjacent topics

SYSTEM_PROMPT = """
You are ImmigrationIQ, a knowledgeable assistant specializing in US immigration,
visas, and related topics for people living or working in the United States.

Rules:
- Prioritize the provided context from official government sources.
- If the context is relevant, base your answer on it and cite the source URL(s).
- If the context is partially relevant or the question is related to immigration
  (e.g. taxes for visa holders, work authorization, travel rules, student status),
  use your general knowledge to supplement and clearly state which parts come
  from official sources vs. general knowledge.
- Only trigger the fallback if the question is completely unrelated to immigration,
  visas, or life in the US as a foreign national.
- Never provide personal legal advice or predict case outcomes.
- Keep answers clear, structured, and easy to understand.
- If the question involves a specific visa type, mention relevant form numbers
  or processing steps if they appear in the context.
- For tax questions from visa holders, always recommend consulting a tax
  professional familiar with nonresident alien taxation.
"""

FALLBACK_RESPONSE = """I don't have specific documents about this in my current sources.

However, if this is related to your immigration status or life in the US as a visa holder, here are helpful resources:
- 🌐 [USCIS](https://www.uscis.gov) — visa applications, status, work authorization
- 🌐 [travel.state.gov](https://travel.state.gov) — consular appointments, visa categories
- 🌐 [IRS for International Taxpayers](https://www.irs.gov/individuals/international-taxpayers) — taxes for F1, H1B, and other visa holders
- 🌐 [Department of Labor](https://www.dol.gov) — work authorization and labor rights

For case-specific guidance, consult a licensed immigration attorney."""


# ── Request / Response Models ─────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str

class Source(BaseModel):
    url: str
    topic: str
    scraped_date: str

class QueryResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    answer: str
    sources: list[Source]
    model_used: str


# ── Query Rewriter ────────────────────────────────────────────────────
def rewrite_query(question: str) -> str:
    """Expand user query with immigration-specific terminology for better retrieval."""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a query rewriter for a US immigration law database. "
                        "Rewrite the user's question to include relevant immigration, "
                        "visa, tax, and legal terminology that would help retrieve "
                        "better results from official government documents. "
                        "Return only the rewritten query, nothing else. "
                        "Keep it under 200 characters."
                    )
                },
                {"role": "user", "content": question}
            ],
            max_tokens=100,
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except OpenAIError:
        return question   # fall back to original if rewrite fails


# ── Health Check ──────────────────────────────────────────────────────
@app.get("/health")
def health():
    try:
        collections = qdrant.get_collections().collections
        qdrant_status = "ok" if collections is not None else "empty"
    except Exception as e:
        qdrant_status = f"error: {str(e)}"

    return {
        "api": "ok",
        "qdrant": qdrant_status,
        "collection": COLLECTION
    }


# ── Stats Endpoint ────────────────────────────────────────────────────
@app.get("/stats")
def stats():
    try:
        info = qdrant.get_collection(COLLECTION)
        return {
            "total_vectors": info.points_count,
            "collection": COLLECTION
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Core Query Endpoint ───────────────────────────────────────────────
@app.post("/ask", response_model=QueryResponse)
def ask(request: QueryRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if len(question) > 1000:
        raise HTTPException(status_code=400, detail="Question too long. Max 1000 characters.")

    # ── Step 1: Rewrite query for better retrieval ────────────────────
    rewritten_question = rewrite_query(question)

    # ── Step 2: Embed the rewritten question ─────────────────────────
    try:
        embedding_response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=rewritten_question
        )
        query_vector = embedding_response.data[0].embedding
    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"Embedding API error: {str(e)}")

    # ── Step 3: Similarity search in Qdrant ──────────────────────────
    try:
        results = qdrant.search(
            collection_name=COLLECTION,
            query_vector=query_vector,
            limit=TOP_K,
            score_threshold=SCORE_THRESHOLD,
            with_payload=True,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Vector search error: {str(e)}")

    # ── Step 4: Build context from retrieved chunks ───────────────────
    context_blocks = []
    seen_urls = set()
    sources = []

    for r in results:
        payload = r.payload
        url   = payload.get("source_url", "Unknown")
        topic = payload.get("topic", "General")
        date  = payload.get("scraped_date", "Unknown")
        text  = payload.get("text", "")

        context_blocks.append(f"[Source: {url}]\n{text}")

        if url not in seen_urls:
            sources.append(Source(url=url, topic=topic, scraped_date=date))
            seen_urls.add(url)

    # ── Step 5: No relevant docs found → return friendly fallback ─────
    if not context_blocks:
        return QueryResponse(
            answer=FALLBACK_RESPONSE,
            sources=[],
            model_used=LLM_MODEL
        )

    context = "\n\n---\n\n".join(context_blocks)

    # ── Step 6: LLM answer generation ────────────────────────────────
    try:
        chat_response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Context from official US government sources:\n\n"
                    f"{context}\n\n"
                    f"Question: {question}"
                )}
            ],
            temperature=0.2,
            max_tokens=1024
        )
    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"LLM API error: {str(e)}")

    answer = chat_response.choices[0].message.content

    return QueryResponse(
        answer=answer,
        sources=sources,
        model_used=LLM_MODEL
    )