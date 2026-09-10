"""The prompts. Kept in one file so the wording is easy to tweak during the
quality-testing loop without hunting through the pipeline code."""
from __future__ import annotations

# The exact sentence the model is told to use when the sources don't answer the
# question. We also detect this phrase to set the "answered = false" flag.
REFUSAL_SENTENCE = "The provided papers don't address this question."


DECOMPOSE_PROMPT = """You split a research question into at most {max_subs} focused sub-questions.
Only split when the question genuinely has separate parts (for example it compares two things, or asks about two topics). If it is already a single focused question, return it unchanged as one line.

Return ONLY the sub-questions, one per line, no numbering, no extra text.

Question: {question}
Sub-questions:"""


DRAFT_SYSTEM = (
    "You answer questions strictly from the provided sources. "
    "You never use outside knowledge and never guess."
)

DRAFT_PROMPT = """Answer the question using ONLY the numbered sources below.

Rules:
- Cite every factual sentence with the source number(s) it comes from, like [1] or [2][3]. Put the marker at the end of the sentence.
- If the question has multiple parts, use bullet points and address each part.
- Use only what the sources say. Do not add outside facts.
- If the sources do not contain the answer, reply with exactly this one sentence and nothing else: {refusal}

Sources:
{sources}

Question: {question}

Answer:"""
