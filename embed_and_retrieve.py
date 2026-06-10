"""
Milestone 4 — Embedding, Vector Store & Retrieval
CSUMB Student Clubs RAG Pipeline

Pipeline stage:  Chunking → [Embedding + ChromaDB] → Retrieval
Embedding model: all-MiniLM-L6-v2 (sentence-transformers, runs locally)
Vector store:    ChromaDB (persisted to ./chroma_db/)
Top-k:           4 chunks per query

Install:
    pip install sentence-transformers chromadb

Usage:
    # 1. Build the database (run once):
    python embed_and_retrieve.py --build

    # 2. Query it:
    python embed_and_retrieve.py --query "How do I register a new club at CSUMB?"

    # 3. Run all 5 eval questions at once:
    python embed_and_retrieve.py --eval
"""

import argparse
import json
import sys

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CHUNKS_FILE   = "chunks.json"
CHROMA_DIR    = "./chroma_db"
COLLECTION    = "csumb_clubs"
EMBED_MODEL   = "all-MiniLM-L6-v2"
TOP_K         = 4

# Evaluation queries from planning.md
EVAL_QUERIES = [
    "Where should a student go to start or register a new club at CSUMB?",
    "What is the difference between ICC and SCC clubs?",
    "Where can an ICC club find funding forms or templates?",
    "What platform is used to browse or join CSUMB student organizations?",
    "Where can sports clubs find their constitution, code of conduct, or tier chart?",
]

# ---------------------------------------------------------------------------
# Step 1 — Load embedding model
# ---------------------------------------------------------------------------

def load_model() -> SentenceTransformer:
    print(f"Loading embedding model '{EMBED_MODEL}' ...")
    model = SentenceTransformer(EMBED_MODEL)
    print("  Model ready.")
    return model


# ---------------------------------------------------------------------------
# Step 2 — Connect to ChromaDB
# ---------------------------------------------------------------------------

def get_client() -> chromadb.Client:
    """
    Returns a persistent ChromaDB client backed by CHROMA_DIR.
    The database is created on first run and reused on subsequent runs.
    """
    return chromadb.PersistentClient(path=CHROMA_DIR)


def get_collection(client: chromadb.Client, create: bool = False):
    """
    Get (or create) the ChromaDB collection.

    ChromaDB stores three things per entry:
      - id         : unique string key for the record
      - embedding  : the vector we computed with sentence-transformers
      - document   : the raw chunk text (used for display after retrieval)
      - metadata   : any extra fields we want back at query time
                     (source_title, source_url, source_id, token_est)

    `get_or_create_collection` is idempotent — safe to call every run.
    """
    if create:
        # Wipe and recreate so re-runs don't duplicate data
        try:
            client.delete_collection(COLLECTION)
            print(f"  Deleted existing collection '{COLLECTION}'.")
        except Exception:
            pass  # didn't exist yet — that's fine
        collection = client.create_collection(
            name=COLLECTION,
            # cosine distance is standard for sentence-transformer embeddings
            metadata={"hnsw:space": "cosine"},
        )
        print(f"  Created new collection '{COLLECTION}'.")
    else:
        collection = client.get_collection(COLLECTION)

    return collection


# ---------------------------------------------------------------------------
# Step 3 — Embed chunks and store in ChromaDB
# ---------------------------------------------------------------------------

def build_database(chunks_file: str = CHUNKS_FILE) -> None:
    """
    Reads chunks.json, embeds every chunk, and stores them in ChromaDB.

    ChromaDB's collection.add() takes parallel lists:
      ids        — must be unique strings; we reuse chunk_id from ingest.py
      embeddings — list of float vectors, one per chunk
      documents  — list of raw text strings (stored verbatim for retrieval display)
      metadatas  — list of dicts; values must be str/int/float (no nested objects)

    We batch in groups of 100 to avoid memory spikes on large corpora.
    """
    print(f"\n=== BUILD: Loading chunks from {chunks_file} ===")
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"  Loaded {len(chunks)} chunks.")

    model     = load_model()
    client    = get_client()
    collection = get_collection(client, create=True)

    BATCH = 100
    total  = len(chunks)

    for start in range(0, total, BATCH):
        batch = chunks[start : start + BATCH]
        end   = min(start + BATCH, total)
        print(f"  Embedding chunks {start}–{end-1} ...")

        texts = [c["text"] for c in batch]

        # encode() returns a numpy array; .tolist() converts to plain Python
        # lists, which is what ChromaDB expects.
        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        collection.add(
            ids        = [c["chunk_id"]    for c in batch],
            embeddings = embeddings,
            documents  = texts,
            metadatas  = [
                {
                    "source_title": c["source_title"],
                    "source_url":   c["source_url"],
                    "source_id":    c["source_id"],
                    "token_est":    c["token_est"],
                }
                for c in batch
            ],
        )

    print(f"\n  Done. {total} chunks stored in '{CHROMA_DIR}/{COLLECTION}'.")


# ---------------------------------------------------------------------------
# Step 4 — Retrieval function
# ---------------------------------------------------------------------------

def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Embed `query` and return the top_k most relevant chunks from ChromaDB.

    collection.query() returns a dict of parallel lists, all indexed the same:
      results["ids"][0]        — list of chunk ids
      results["documents"][0]  — list of raw chunk texts
      results["metadatas"][0]  — list of metadata dicts
      results["distances"][0]  — list of cosine distances (0 = identical, 2 = opposite)
                                  practical range with cosine + MiniLM: ~0.1 (great) to ~0.8 (weak)

    The [0] index is because ChromaDB supports batched queries; we're only
    sending one query at a time so the outer list always has one element.
    """
    model      = load_model()
    client     = get_client()
    collection = get_collection(client, create=False)

    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings = query_embedding,
        n_results        = top_k,
        include          = ["documents", "metadatas", "distances"],
    )

    # Repack into a clean list of dicts for easy use in Milestone 5
    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append(
            {
                "text":         doc,
                "source_title": meta["source_title"],
                "source_url":   meta["source_url"],
                "distance":     round(dist, 4),
            }
        )

    return hits


# ---------------------------------------------------------------------------
# Step 5 — Pretty-print results
# ---------------------------------------------------------------------------

def print_results(query: str, hits: list[dict]) -> None:
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print(f"{'='*70}")
    for rank, hit in enumerate(hits, 1):
        distance_flag = ""
        if hit["distance"] > 0.6:
            distance_flag = "  ⚠️  HIGH — weak match, check chunk quality"
        elif hit["distance"] < 0.3:
            distance_flag = "  ✅ strong match"

        print(f"\n  [{rank}] distance: {hit['distance']}{distance_flag}")
        print(f"       source:   {hit['source_title']}")
        print(f"       url:      {hit['source_url']}")
        print(f"       text:     {hit['text'][:300].strip()} ...")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Milestone 4 — Embed chunks into ChromaDB and run retrieval."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--build",
        action="store_true",
        help="Embed chunks.json and (re)build the ChromaDB database.",
    )
    group.add_argument(
        "--query",
        type=str,
        metavar="QUESTION",
        help="Retrieve top-k chunks for a single question.",
    )
    group.add_argument(
        "--eval",
        action="store_true",
        help="Run all 5 planning.md evaluation queries and print results.",
    )
    args = parser.parse_args()

    if args.build:
        build_database()

    elif args.query:
        hits = retrieve(args.query)
        print_results(args.query, hits)

    elif args.eval:
        print("\n=== EVAL: Running all 5 evaluation queries ===")
        for q in EVAL_QUERIES:
            hits = retrieve(q)
            print_results(q, hits)


if __name__ == "__main__":
    main()
