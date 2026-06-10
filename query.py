"""
query.py — Generation layer for the CSUMB Student Clubs RAG pipeline.

Retrieves top-k chunks from ChromaDB, builds a grounded prompt, calls
Groq's llama-3.3-70b-versatile, and returns a structured response with
programmatically guaranteed source attribution.

Requires:
    pip install groq python-dotenv
    GROQ_API_KEY set in a .env file (or as an environment variable)
"""

import os
from dotenv import load_dotenv
from groq import Groq

# Import retrieval from Milestone 4
from embed_and_retrieve import retrieve

load_dotenv()

# ---------------------------------------------------------------------------
# LLM client
# ---------------------------------------------------------------------------

_groq_client = None

def get_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY not found. Add it to a .env file:\n"
                "  GROQ_API_KEY=your_key_here\n"
                "Get a free key at https://console.groq.com"
            )
        _groq_client = Groq(api_key=api_key)
    return _groq_client


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a helpful assistant for CSUMB students asking about
student clubs, club registration, funding, and student organizations.

RULES — you must follow these exactly:
1. Answer ONLY using information explicitly stated in the DOCUMENTS block below.
2. Do NOT use any outside knowledge, assumptions, or training data.
3. If the documents do not contain enough information to answer the question,
   respond with exactly: "I don't have enough information on that."
4. Do not speculate, infer, or fill gaps with general knowledge.
5. Keep your answer clear and concise — 1 to 4 sentences is usually enough.
6. Do NOT include a source list in your answer — sources are handled separately."""


def build_user_prompt(question: str, chunks: list[dict]) -> str:
    """
    Build the user-turn message by injecting retrieved chunks as numbered
    DOCUMENTS. Labeling each document makes it easier for the LLM to stay
    grounded and harder to drift into training knowledge.
    """
    docs_block = "\n\n".join(
        f"[Document {i+1}] (Source: {c['source_title']})\n{c['text']}"
        for i, c in enumerate(chunks)
    )
    return (
        f"DOCUMENTS:\n{docs_block}\n\n"
        f"QUESTION: {question}\n\n"
        f"Answer using only the documents above."
    )


# ---------------------------------------------------------------------------
# Main ask() function — used by app.py
# ---------------------------------------------------------------------------

def ask(question: str, top_k: int = 4) -> dict:
    """
    End-to-end RAG call. Returns:
      {
        "answer":  str,          # LLM response grounded in retrieved chunks
        "sources": list[str],    # programmatically collected source titles+urls
        "chunks":  list[dict],   # raw retrieved chunks (for debugging)
      }

    Source attribution is programmatic: we collect source_title and source_url
    from every retrieved chunk BEFORE the LLM is called, so the source list
    is guaranteed regardless of what the model decides to say.
    """
    # 1. Retrieve
    chunks = retrieve(question, top_k=top_k)

    # 2. Collect sources programmatically (not left to the LLM)
    seen = set()
    sources = []
    for c in chunks:
        key = c["source_url"]
        if key not in seen:
            seen.add(key)
            sources.append(f"{c['source_title']} — {c['source_url']}")

    # 3. Build prompt and call Groq
    user_prompt = build_user_prompt(question, chunks)
    client = get_client()

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.0,   # deterministic — grounding works better at temp=0
        max_tokens=512,
    )

    answer = completion.choices[0].message.content.strip()

    return {
        "answer":  answer,
        "sources": sources,
        "chunks":  chunks,   # available for debug printing in app.py
    }


# ---------------------------------------------------------------------------
# CLI smoke test — python query.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    TEST_QUERIES = [
        # Should answer from SELD / MyRaft chunks
        "Where should a student go to start or register a new club at CSUMB?",
        # Should answer from ICC vs SCC chunks
        "What is the difference between ICC and SCC clubs?",
        # Should trigger the fallback — not covered by any source
        "What is the GPA requirement to join a club at CSUMB?",
    ]

    for q in TEST_QUERIES:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        result = ask(q)
        print(f"\nA: {result['answer']}")
        print("\nSources:")
        for s in result["sources"]:
            print(f"  • {s}")
        print(f"\nTop chunk distance: {result['chunks'][0]['distance']}")
