from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024,      # ← increased from 512 (captures full policy sections)
    chunk_overlap=150,    # ← increased from 50 (more context preserved at boundaries)
    separators=[
        "\n\n\n",         # major section breaks
        "\n\n",           # paragraph breaks
        "\n",             # line breaks
        ". ",             # sentence boundaries
        " ",              # word boundaries
        ""                # character fallback
    ]
)


def chunk_text(text: str, url: str, topic: str, scraped_date: str) -> list[dict]:
    chunks = splitter.split_text(text)
    return [
        {
            "text": chunk,
            "source_url": url,
            "topic": topic,
            "scraped_date": scraped_date
        }
        for chunk in chunks
        if len(chunk.strip()) > 100    # ← increased from 50 (filters more noise)
    ]