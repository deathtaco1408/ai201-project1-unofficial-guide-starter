# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

how students can start, register, fund, and manage student clubs at CSUMB. This knowledge is valuable because the information is spread across multiple CSUMB pages, MyRaft pages, ICC resources, SCC documents, and policy documents. It can be hard for students to know which source applies to their situation, especially when distinguishing between general clubs, ICC clubs, and sports clubs.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Student Clubs and Organizations | General CSUMB overview of student clubs, organizations, involvement, and MyRaft. | https://csumb.edu/seld/clubs-organizations/ |
| 2 | MyRaft club directory / groups list | Directory of active CSUMB groups and organization categories. | https://myraft.csumb.edu/club_signup?view=all |
| 3 | Inter-Club Council home page | Main page for ICC, which supports recognized non-sport clubs. | https://myraft.csumb.edu/ICC/ |
| 4 | ICC Useful Links | Collection of important club forms, templates, policies, and guides. | https://myraft.csumb.edu/icc/useful-links/ |
| 5 | ICC Documents | Archive of ICC governing documents, agendas, minutes, and policies. | https://myraft.csumb.edu/icc/documents/ |
| 6 | ICC Example event page | Example of ICC General Council meeting information and expectations. | https://myraft.csumb.edu/icc/rsvp_boot?id=1959463 |
| 7 | SCC Handbook Resource / How to Start a Sports Club | Sports-club-specific guidance for starting and managing a sport club. | https://myraft.csumb.edu/scc/handbook-resource/ |
| 8 | SCC Documents | Sports Club Council documents, constitution, code of conduct, tier chart, and meeting records. | https://myraft.csumb.edu/scc/documents/ |
| 9 | Associated Students | Information about student government and student organization support/funding. | https://csumb.edu/seld/associated-students/ |
| 10 | Student Engagement and Leadership Development (SELD) | Office page connected to club registration, advising, leadership, and student engagement support. | https://csumb.edu/clubs/register-club-or-organization/?_search=icc+ |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**
     800–1,000 tokens per chunk (recommended to me by the chatgpt)
**Overlap:**
     100–150 tokens 
**Reasoning:**
     The CSUMB and MyRaft documents seem to contain short sections, lists, policies, and links. A chunk size of around 800–1,000 tokens is should be large enough to keep related instructions together, such as registration steps, funding rules, or meeting requirements while a 100–150 token overlap helps prevent important context from being split across chunk boundaries, especially when a policy explanation continues across headings or bullet lists.
---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
     all-MiniLM-L6-v2 using sentence-transformers

**Top-k:**
     Retrieve the top 4 chunks per user query.

**Production tradeoff reflection:**
     For this class project, all-MiniLM-L6-v2 is a good choice because it is lightweight, fast, free to run locally, accurate enough for short policy and FAQ-style text, and it is already the deafult from groq from what I can tell. If this were deployed for real CSUMB students, I would consider a stronger embedding model with better accuracy and longer context support. I would weigh tradeoffs such as retrieval accuracy, cost, latency, ability to handle long policy documents, and whether the model performs well on campus-specific terms like ICC, SCC, MyRaft, SELD, and Associated Students.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | Where should a student go to start or register a new club at CSUMB? | They should use the CSUMB “Start a Club or Organization” registration page and follow the club registration process through SELD/MyRaft. |
| 2 | What is the difference between ICC and SCC clubs? | ICC supports general student organizations, while SCC supports sports clubs and sport-related organizations. |
| 3 | Where can an ICC club find funding forms or templates? | The ICC Useful Links page includes resources such as funding proposal templates and request-to-use-funds forms. |
| 4 | What platform is used to browse or join CSUMB student organizations? | MyRaft is used to browse groups, view organizations, and find involvement opportunities. |
| 5 | Where can sports clubs find their constitution, code of conduct, or tier chart? | Sports clubs can find these materials on the SCC Documents page. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Information is spread across multiple sites.
Club information is split between CSUMB pages, MyRaft pages, ICC pages, SCC pages, and Associated Students pages. This could cause retrieval to return incomplete answers if the system only finds one source instead of combining multiple relevant chunks.

2. Some documents may be policy-heavy or link-heavy.
Pages like ICC Useful Links and SCC Documents may contain many links with short descriptions. If chunking is too large, unrelated policies may be grouped together. If chunking is too small, the system may retrieve a link title without enough surrounding context.

3. Rules may change by semester or academic year.
Club registration dates, forms, funding templates, and officer requirements may change. The system should preserve source URLs and ideally include dates or document titles when available.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

     flowchart LR
    A[Document Ingestion<br>requests + BeautifulSoup or manual HTML/PDF collection] --> B[Chunking<br>Custom chunk_text function<br>800-1000 tokens, 100-150 overlap]
    B --> C[Embedding + Vector Store<br>sentence-transformers all-MiniLM-L6-v2<br>FAISS or Chroma]
    C --> D[Retrieval<br>Top-k = 4 most relevant chunks]
    D --> E[Generation<br>LLM answers using retrieved chunks<br>with source citations]

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
     I will use Claude + Claude Code to help implement the document ingestion and chunking code since we already have a subscription to it as a codepath student. I also have a Chatgpt subscription due to CSUMB, so I will also use that, if nothing else, to have a second opinion on stuff. I will give the AI my Documents section and Chunking Strategy section, including the source URLs, chunk size, overlap size, and requirement to preserve source metadata. I expect it to produce Python functions that load each source, extract readable text, split text into chunks, and save each chunk with its source URL and title. I will verify the output by checking that each source is represented, chunks are not empty, and source metadata is preserved.

**Milestone 4 — Embedding and retrieval:**
     Same as above (Claude + Claude Code with Chatgpt serving as a second opinion of sorts) I will give the AI my Retrieval Approach section, including the embedding model all-MiniLM-L6-v2 and top-k value of 4. I expect it to produce code that embeds chunks, stores vectors in FAISS or Chroma, and retrieves the most relevant chunks for a query. I will verify it by running my evaluation questions and checking whether the retrieved chunks come from the correct CSUMB, ICC, or SCC sources.

**Milestone 5 — Generation and interface:**
     Same as above; I will provide the AI with my Evaluation Plan, Retrieval Approach, and requirement that answers cite source titles or URLs. I expect it to produce code that takes a user question, retrieves relevant chunks, sends them to the LLM, and generates a grounded answer. I will verify the system by running the five test questions and checking whether the answers match the expected answers and include appropriate source attribution.

