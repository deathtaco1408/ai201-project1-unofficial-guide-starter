"""
Milestone 3 — Document Ingestion & Chunking
CSUMB Student Clubs RAG Pipeline

Sources: 10 CSUMB/MyRaft/ICC/SCC pages (see planning.md)
         + PDFs linked from pages that have a `scrape_pdfs` flag
Chunks:  800–1000 tokens, 100–150 token overlap
Output:  chunks saved to chunks.json with source metadata

Install:
    pip install requests beautifulsoup4 pdfplumber
"""

import io
import json
import time
import requests
import pdfplumber
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

SOURCES = [
    {
        "id": 1,
        "title": "Student Clubs and Organizations",
        "url": "https://csumb.edu/seld/clubs-organizations/",
    },
    {
        "id": 2,
        "title": "MyRaft Club Directory",
        "url": "https://myraft.csumb.edu/club_signup?view=all",
    },
    {
        "id": 3,
        "title": "Inter-Club Council Home",
        "url": "https://myraft.csumb.edu/ICC/",
    },
    {
        "id": 4,
        "title": "ICC Useful Links",
        "url": "https://myraft.csumb.edu/icc/useful-links/",
    },
    {
        "id": 5,
        "title": "ICC Documents",
        "url": "https://myraft.csumb.edu/icc/documents/",
        "scrape_pdfs": True,   # follow and extract linked PDFs from this page
    },
    {
        "id": 6,
        "title": "ICC General Council Meeting Info",
        "url": "https://myraft.csumb.edu/icc/rsvp_boot?id=1959463",
    },
    {
        "id": 7,
        "title": "SCC Handbook / How to Start a Sports Club",
        "url": "https://myraft.csumb.edu/scc/handbook-resource/",
    },
    {
        "id": 8,
        "title": "SCC Documents",
        "url": "https://myraft.csumb.edu/scc/documents/",
    },
    {
        "id": 9,
        "title": "Associated Students",
        "url": "https://csumb.edu/seld/associated-students/",
    },
    {
        "id": 10,
        "title": "SELD Club Registration",
        "url": "https://csumb.edu/clubs/register-club-or-organization/",
    },
]

# ---------------------------------------------------------------------------
# Step 1 — Fetch & extract text
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; CSUMBClubBot/1.0; +for-class-project)"
    )
}


def fetch_text(url: str) -> str:
    """
    Fetch a URL and return its visible text, stripping nav/footer/script noise.
    Returns empty string on failure.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [WARN] Could not fetch {url}: {e}")
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove noisy elements
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    # Prefer <main> or <article> if present; otherwise fall back to <body>
    content = soup.find("main") or soup.find("article") or soup.body
    if content is None:
        return ""

    # Collapse whitespace
    text = content.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]          # drop blank lines
    return "\n".join(lines)



# ---------------------------------------------------------------------------
# Step 1b — PDF extraction
# ---------------------------------------------------------------------------

def fetch_pdf_links(page_url: str) -> list[dict]:
    """
    Scrape a page and return all links that point to PDF files.
    Returns a list of {"title": str, "url": str} dicts.
    """
    try:
        resp = requests.get(page_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [WARN] Could not fetch page for PDF links {page_url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    from urllib.parse import urljoin, urlparse

    pdf_links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        # Resolve relative URLs
        full_url = urljoin(page_url, href)
        # Only keep .pdf links, deduplicate
        if full_url.lower().endswith(".pdf") and full_url not in seen:
            seen.add(full_url)
            title = a.get_text(strip=True) or urlparse(full_url).path.split("/")[-1]
            pdf_links.append({"title": title, "url": full_url})

    print(f"  Found {len(pdf_links)} PDF link(s) on page.")
    return pdf_links


def extract_pdf_text(pdf_url: str) -> str:
    """
    Download a PDF from `pdf_url` and extract its text using pdfplumber.
    Returns empty string on failure.
    """
    try:
        resp = requests.get(pdf_url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    [WARN] Could not download PDF {pdf_url}: {e}")
        return ""

    try:
        with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            full_text = "\n".join(pages_text)
    except Exception as e:
        print(f"    [WARN] Could not parse PDF {pdf_url}: {e}")
        return ""

    # Collapse whitespace the same way as HTML pages
    lines = [line.strip() for line in full_text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)



def estimate_tokens(text: str) -> int:
    """
    Rough token estimate: 1 token ≈ 4 characters (good enough for chunking).
    """
    return len(text) // 4


def chunk_text(
    text: str,
    chunk_tokens: int = 900,
    overlap_tokens: int = 125,
) -> list[str]:
    """
    Split `text` into overlapping chunks targeting `chunk_tokens` tokens each.

    Strategy:
      - Split on newlines to keep paragraph/list structure intact.
      - Accumulate lines until the chunk reaches `chunk_tokens`.
      - Slide back `overlap_tokens` worth of content before starting the next chunk,
        so context is never lost at a boundary.
    """
    chunk_chars = chunk_tokens * 4
    overlap_chars = overlap_tokens * 4

    lines = text.split("\n")
    chunks = []
    current = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1  # +1 for the newline we stripped

        # If adding this line would overflow, flush the current chunk
        if current_len + line_len > chunk_chars and current:
            chunk_text_str = "\n".join(current)
            chunks.append(chunk_text_str)

            # Roll back by overlap_chars to seed the next chunk
            rollback = []
            rollback_len = 0
            for prev_line in reversed(current):
                if rollback_len + len(prev_line) + 1 > overlap_chars:
                    break
                rollback.insert(0, prev_line)
                rollback_len += len(prev_line) + 1

            current = rollback
            current_len = rollback_len

        current.append(line)
        current_len += line_len

    # Flush the final chunk
    if current:
        chunks.append("\n".join(current))

    return chunks


# ---------------------------------------------------------------------------
# Step 3 — Build chunk records with metadata
# ---------------------------------------------------------------------------

def build_chunks(sources: list[dict]) -> list[dict]:
    """
    Fetch each source, chunk its text, and return a flat list of chunk dicts:
      {
        "chunk_id":    "src1_chunk0",
        "source_id":   1,
        "source_title": "Student Clubs and Organizations",
        "source_url":  "https://...",
        "text":        "...",
        "token_est":   742,
      }

    For sources with `scrape_pdfs: True`, the page itself is also ingested,
    then every linked PDF is downloaded, extracted, and chunked separately,
    each with its own source_title and source_url pointing to the PDF.
    """
    all_chunks = []

    for source in sources:
        print(f"Fetching [{source['id']:02d}] {source['title']} ...")
        text = fetch_text(source["url"])

        if not text:
            print(f"  [SKIP] No text extracted from page.")
        else:
            token_count = estimate_tokens(text)
            print(f"  Extracted ~{token_count} tokens from page. Chunking ...")
            chunks = chunk_text(text)
            print(f"  → {len(chunks)} chunks produced.")
            for i, chunk in enumerate(chunks):
                all_chunks.append(
                    {
                        "chunk_id": f"src{source['id']}_chunk{i}",
                        "source_id": source["id"],
                        "source_title": source["title"],
                        "source_url": source["url"],
                        "text": chunk,
                        "token_est": estimate_tokens(chunk),
                    }
                )

        # --- PDF sub-ingestion ---
        if source.get("scrape_pdfs"):
            pdf_links = fetch_pdf_links(source["url"])
            for pdf in pdf_links:
                print(f"  Extracting PDF: {pdf['title']} ...")
                pdf_text = extract_pdf_text(pdf["url"])
                if not pdf_text:
                    print(f"    [SKIP] No text from PDF.")
                    continue
                pdf_token_count = estimate_tokens(pdf_text)
                print(f"    ~{pdf_token_count} tokens. Chunking ...")
                pdf_chunks = chunk_text(pdf_text)
                print(f"    → {len(pdf_chunks)} chunks.")
                # Use the page's source_id so they're grouped under ICC Documents
                for i, chunk in enumerate(pdf_chunks):
                    all_chunks.append(
                        {
                            "chunk_id": f"src{source['id']}_pdf_{pdf['title'][:30].replace(' ', '_')}_chunk{i}",
                            "source_id": source["id"],
                            "source_title": f"{source['title']} — {pdf['title']}",
                            "source_url": pdf["url"],
                            "text": chunk,
                            "token_est": estimate_tokens(chunk),
                        }
                    )
                time.sleep(0.5)

        time.sleep(0.5)  # be polite to CSUMB servers

    return all_chunks


# ---------------------------------------------------------------------------
# Step 4 — Save to disk
# ---------------------------------------------------------------------------

def save_chunks(chunks: list[dict], path: str = "documents/chunks.json") -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(chunks)} chunks to {path}")


# ---------------------------------------------------------------------------
# Verification helper
# ---------------------------------------------------------------------------

def verify_chunks(chunks: list[dict]) -> None:
    """
    Quick sanity check:
      - Every source has at least one chunk.
      - No chunk is empty.
      - Metadata fields are all present.
    """
    print("\n--- Verification ---")
    source_ids_seen = {c["source_id"] for c in chunks}
    expected_ids = {s["id"] for s in SOURCES}
    missing = expected_ids - source_ids_seen
    if missing:
        print(f"[WARN] Missing chunks for source IDs: {missing}")
    else:
        print("[OK] All sources have at least one chunk.")

    empty = [c["chunk_id"] for c in chunks if not c["text"].strip()]
    if empty:
        print(f"[WARN] Empty chunks: {empty}")
    else:
        print("[OK] No empty chunks.")

    required_keys = {"chunk_id", "source_id", "source_title", "source_url", "text", "token_est"}
    bad_meta = [c["chunk_id"] for c in chunks if not required_keys.issubset(c)]
    if bad_meta:
        print(f"[WARN] Chunks missing metadata keys: {bad_meta}")
    else:
        print("[OK] All chunks have required metadata fields.")

    sizes = [c["token_est"] for c in chunks]
    print(
        f"[INFO] Chunk token stats — "
        f"min: {min(sizes)}, max: {max(sizes)}, "
        f"avg: {sum(sizes)//len(sizes)}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    chunks = build_chunks(SOURCES)
    save_chunks(chunks, "chunks.json")
    verify_chunks(chunks)
