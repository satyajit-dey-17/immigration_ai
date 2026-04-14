import streamlit as st
import requests
import os
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="ImmigrationIQ",
    page_icon="🗽",
    layout="centered"
)

# ── Session State Init ────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# ── Helpers ───────────────────────────────────────────────────────────
def fmt_date(iso_str: str) -> str:
    try:
        return datetime.fromisoformat(iso_str).strftime("%b %d, %Y")
    except Exception:
        return iso_str[:10]


def query_api(question: str):
    try:
        response = requests.post(
            f"{API_URL}/ask",
            json={"question": question},
            timeout=30
        )
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, "❌ Cannot connect to the API. Make sure the backend is running."
    except requests.exceptions.Timeout:
        return None, "⏱️ Request timed out. Try again."
    except Exception as e:
        return None, f"Something went wrong: {str(e)}"


def handle_question(question: str):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching immigration documents..."):
            data, error = query_api(question)
            if error:
                st.error(error)
                return
            answer  = data["answer"]
            sources = data.get("sources", [])
            st.markdown(answer)
            if sources:
                with st.expander("📎 Sources"):
                    for src in sources:
                        st.markdown(
                            f"- [{src['url']}]({src['url']}) "
                            f"— *{src['topic']}* "
                            f"— scraped `{fmt_date(src['scraped_date'])}`"
                        )
            st.session_state.messages.append({
                "role":    "assistant",
                "content": answer,
                "sources": sources
            })


# ── Header ────────────────────────────────────────────────────────────
st.title("🗽 ImmigrationIQ")
st.caption("Ask any question about US immigration — powered by official government sources.")
st.warning(
    "⚠️ This tool provides **informational answers only** and is not legal advice. "
    "Always consult a licensed immigration attorney for your specific situation."
)
st.divider()

# ── Render chat history ───────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📎 Sources"):
                for src in msg["sources"]:
                    st.markdown(
                        f"- [{src['url']}]({src['url']}) "
                        f"— *{src['topic']}* "
                        f"— scraped `{fmt_date(src['scraped_date'])}`"
                    )

# ── Handle pending question from sidebar ──────────────────────────────
if st.session_state.pending_question:
    q = st.session_state.pending_question
    st.session_state.pending_question = None
    handle_question(q)

# ── Chat input ────────────────────────────────────────────────────────
elif prompt := st.chat_input("e.g. What are the H-1B visa requirements?"):
    handle_question(prompt)

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📚 About")
    st.markdown("""
    **ImmigrationIQ** answers your US immigration questions using
    official government sources including:
    - 🏛️ [USCIS](https://www.uscis.gov)
    - ✈️ [travel.state.gov](https://travel.state.gov)
    - 📋 [Federal Register](https://www.federalregister.gov)
    - 💼 [Department of Labor](https://www.dol.gov)
    """)

    try:
        stats = requests.get(f"{API_URL}/stats", timeout=5).json()
        st.metric("📊 Documents indexed", f"{stats['total_vectors']:,}")
    except Exception:
        pass

    st.divider()
    st.header("💡 Example Questions")
    examples = [
        "What documents do I need for an H-1B visa?",
        "How long does green card processing take?",
        "Can I travel while my EAD renewal is pending?",
        "What is the difference between EB-2 and EB-3?",
        "How do I extend my F-1 OPT?",
        "What are the latest asylum rule changes?",
    ]
    for q in examples:
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q
            st.rerun()

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()