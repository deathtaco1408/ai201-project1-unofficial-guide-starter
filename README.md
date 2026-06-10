# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

     how students can start, register, fund, and manage student clubs at CSUMB. This knowledge is valuable because the information is spread across multiple CSUMB pages, MyRaft pages, ICC resources, SCC documents, and policy documents. It can be hard for students to know which source applies to their situation, especially when distinguishing between general clubs, ICC clubs, and sports clubs.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

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

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**
     800–1,000 tokens per chunk (recommended to me by the chatgpt)
**Overlap:**
     100-150 tokens
**Why these choices fit your documents:**
     The CSUMB and MyRaft documents seem to contain short sections, lists, policies, and links. A chunk size of around 800–1,000 tokens should be large enough to keep related instructions together, such as registration steps, funding rules, or meeting requirements while a 100–150 token overlap helps prevent important context from being split across chunk boundaries, especially when a policy explanation continues across headings or bullet lists.
**Final chunk count:**
     113
---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

**Production tradeoff reflection:**
     For this class project, all-MiniLM-L6-v2 is a good choice because it is lightweight, fast, free to run locally, accurate enough for short policy and FAQ-style text, and it is already the deafult from groq from what I can tell. After playing around with it a bit, if this were deployed for real CSUMB students, I would consider a stronger embedding model with better accuracy and longer context support. Definitely would feed it more information and prioritize accuracy over speed.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
     1. the llm never gets a plain question. query.py wraps the question in a "Documents = " ensuring the llm only answers based on the chunks it gets from chunks.json
     2. The system prompt in query.py has six numbered rules that explicitly forbid the model from going outside the documents, one of which states "If the documents do not contain enough information… respond with exactly: 'I don't have enough information on that.'"
     3. temperature=0.0, so the model is not allowed to sway away from documents, for good and bad. may need to fix that.
**How source attribution is surfaced in the response:**
     In query.py, the sources list is built from the retrieved chunk metadata before client.chat.completions.create() is called and then is passed along to app.py to show.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Where should a student go to start or register a new club at CSUMB? | They should use the CSUMB “Start a Club or Organization” registration page and follow the club registration process through SELD/MyRaft. | To start or register a new club at CSUMB, a student should reach out to the SCC email, as the registration process occurs during November and April, and they can help begin the process. Additionally, students can contact the Student Engagement and Leadership Development Office for help with getting involved on campus and registering a new club. | Relevant | Accurate |
| 2 | What is the difference between ICC and SCC clubs? | ICC supports general student organizations, while SCC supports sports clubs and sport-related organizations. | I don't have enough information on that. | Relevant | Partially accurate |
| 3 | Where can an ICC club find funding forms or templates? | The ICC Useful Links page includes resources such as funding proposal templates and request-to-use-funds forms. | The cumulative and previous semester GPA requirement for officer eligibility in a recognized student organization at CSUMB is at least 2.3. | Relevant | Accurate |
| 4 | What platform is used to browse or join CSUMB student organizations? | MyRaft is used to browse groups, view organizations, and find involvement opportunities. | MyRaft is the platform used to manage membership, share updates, and promote events for CSUMB student organizations, and it is the best way to explore opportunities and stay connected. | Relevant | Accurate
| 5 | Where can sports clubs find their constitution, code of conduct, or tier chart? | Sports clubs can find these materials on the SCC Documents page. | I don't have enough information on that. | Relevant | Partially accurate

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**
     Where can sports clubs find their constitution, code of conduct, or tier chart?

     What is the difference between ICC and SCC clubs?

**What the system returned:**

     " I don't have enough information on that. " for both

**Root cause (tied to a specific pipeline stage):**

     In both cases the system accurately tried to retrieve the Chunks/documents on both the ICC and SCC, but was unable to provide a response; this is both a problem with my sources and how CSUMB handles alot of its documentation regarding clubs and other on-campus activities which is to say that it is not regaularly updated. this is not to say that I fed my model dead links so much as the only active links that are not dead are primarily from the ICC while the SCC has deleted alot of their material online, but have not gotten around to posting the updated material anywhere I can access either on the school webpage or myraft.

**What you would change to fix it:**

     I would need to wait till the school updates the SCC documentation or I would increment the temperature parameter from 0.0 to something slightly higher so the system can infer slightly from the ICC documentation what should be required for the SCC material

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
     The spec added alot of constraints and gave me something to lean back on when i could have easily been overwhelmed.
     I think the most important thing it did was give me a clear path that i could follow while also stopping me from overthinking certain things and wasting time on useless methods or functions.
**One way your implementation diverged from the spec, and why:**
     The only thing I can think of that is remotely a divergence from the spec is the addition of the pdf documents I downloaded from ICC Useful Links and ICC Documents to add additional context to sources 4 and 5 as well as changing ingest.py to read these documents as if they were sub documents of those 2 sources. as the original way of doing it was to access the link for sources 4 and 5 and then to access the links on each of those pages, but I found that that led to way less chunks than I would have liked (75 chunks)

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
     I followed the instructions for the project, so:
          1. Use your planning.md as a prompt to an AI tool (Claude, Copilot, ChatGPT) to generate your ingestion and chunking code. Share your Documents section (what file types and sources you have), your Chunking Strategy section, and your pipeline diagram.

          2. Use your planning.md Retrieval Approach section and your pipeline diagram to prompt an AI tool to generate your embedding and retrieval code.

          3. Use your planning.md and pipeline diagram to prompt an AI tool to generate the generation and interface code. Your prompt should include: your grounding requirement (answers from retrieved context only, with source attribution), the output format you want (answer + source list), and the Gradio skeleton structure if you're using it.
     
     Specifically, I copied and pasted those specific instructions into Claude for each of the milestones alongside a small addendum asking it to explain to me how code it generated works, what packages it used, why it used them, and what each of the functions in those packages were.

     I also asked it to generate test cases in each of the files so that I could run each of them separately and see what happens as well as a mode in, embed_and_retrieve.py and query.py that would allow me to test individual queries and see what happens.
- *What it produced:*
     it made files as I asked.  it seems that doing each of the milestones sequentially seems to have minimized the risk of Claude generating the code simulatneously and thus causing more issues to arise. 
- *What I changed or overrode:*
     the only changes that I had to get Claude to fix was a misordering of methods that defined a method after it was to be used by five other methods, but that was fairly straightforward.
**Instance 2**

- *What I gave the AI:*
     I followed the instructions for the project, so:
          1. Use your planning.md as a prompt to an AI tool (Claude, Copilot, ChatGPT) to generate your ingestion and chunking code. Share your Documents section (what file types and sources you have), your Chunking Strategy section, and your pipeline diagram.

          2. Use your planning.md Retrieval Approach section and your pipeline diagram to prompt an AI tool to generate your embedding and retrieval code.

          3. Use your planning.md and pipeline diagram to prompt an AI tool to generate the generation and interface code. Your prompt should include: your grounding requirement (answers from retrieved context only, with source attribution), the output format you want (answer + source list), and the Gradio skeleton structure if you're using it.
     
     Specifically, I copied and pasted those specific instructions into Claude for each of the milestones alongside a small addendum asking it to explain to me how code it generated works, what packages it used, why it used them, and what each of the functions in those packages were.

     I also asked it to generate test cases in each of the files so that I could run each of them separately and see what happens as well as a mode in, embed_and_retrieve.py and query.py that would allow me to test individual queries and see what happens.
- *What it produced:*
     it made files as I asked.  it seems that doing each of the milestones sequentially seems to have minimized the risk of Claude generating the code simulatneously and thus causing more issues to arise. 
- *What I changed or overrode:*
     other than ingest.py, the others were left as is. they seemed to work well enough.
