"""
app.py — Gradio interface for the CSUMB Student Clubs RAG chatbot.

Run:
    python app.py
    Open: http://localhost:7860

Requires:
    pip install gradio>=6.9.0
"""

import gradio as gr
from query import ask


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

def handle_query(question: str):
    """
    Called by Gradio on every button click or Enter press.
    Returns two strings: the answer and a formatted source list.
    """
    question = question.strip()
    if not question:
        return "Please enter a question.", ""

    result = ask(question)

    answer = result["answer"]

    # Format sources as a bullet list
    if result["sources"]:
        sources_text = "\n".join(f"• {s}" for s in result["sources"])
    else:
        sources_text = "No sources retrieved."

    return answer, sources_text


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

with gr.Blocks(
    title="CSUMB Student Clubs Assistant",
    theme=gr.themes.Soft(),
) as demo:

    gr.Markdown(
        """
        # 🐦 CSUMB Student Clubs Assistant
        Ask questions about starting, registering, funding, or managing student clubs at CSUMB.
        Answers are drawn only from official CSUMB, ICC, SCC, and MyRaft sources.
        """
    )

    with gr.Row():
        with gr.Column(scale=3):
            inp = gr.Textbox(
                label="Your question",
                placeholder="e.g. How do I register a new club at CSUMB?",
                lines=2,
            )
            btn = gr.Button("Ask", variant="primary")

    with gr.Row():
        with gr.Column(scale=3):
            answer_box = gr.Textbox(
                label="Answer",
                lines=8,
                interactive=False,
            )
        with gr.Column(scale=2):
            sources_box = gr.Textbox(
                label="Retrieved from",
                lines=8,
                interactive=False,
            )

    # Example questions so a viewer immediately understands what to ask
    gr.Examples(
        examples=[
            ["Where should a student go to start or register a new club at CSUMB?"],
            ["What is the difference between ICC and SCC clubs?"],
            ["Where can an ICC club find funding forms or templates?"],
            ["What platform is used to browse or join CSUMB student organizations?"],
            ["Where can sports clubs find their constitution, code of conduct, or tier chart?"],
        ],
        inputs=inp,
        label="Example questions",
    )

    # Wire up both button click and Enter key
    btn.click(handle_query, inputs=inp, outputs=[answer_box, sources_box])
    inp.submit(handle_query, inputs=inp, outputs=[answer_box, sources_box])

if __name__ == "__main__":
    demo.launch()
