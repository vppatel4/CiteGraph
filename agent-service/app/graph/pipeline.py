"""Wire the five steps into a LangGraph state machine and expose one run() call.

The graph is linear except for one branch: after retrieval, if nothing relevant
was found we jump straight to finalize (which returns the honest "not found")
instead of asking the LLM to make something up.

    decompose -> retrieve -> [relevant?] -> draft -> verify -> finalize
                                    \-> finalize
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, StateGraph

from app.graph import nodes


@lru_cache(maxsize=1)
def _build():
    g = StateGraph(dict)
    g.add_node("decompose", nodes.decompose)
    g.add_node("retrieve", nodes.retrieve)
    g.add_node("draft", nodes.draft)
    g.add_node("verify", nodes.verify)
    g.add_node("finalize", nodes.finalize)

    g.set_entry_point("decompose")
    g.add_edge("decompose", "retrieve")
    g.add_conditional_edges(
        "retrieve", nodes.has_relevant, {"draft": "draft", "finalize": "finalize"}
    )
    g.add_edge("draft", "verify")
    g.add_edge("verify", "finalize")
    g.add_edge("finalize", END)
    return g.compile()


def run(user_id: str, question: str, paper_ids: list[str] | None = None) -> dict:
    state = {
        "user_id": user_id,
        "question": question,
        "paper_ids": paper_ids or [],
    }
    result = _build().invoke(state)
    return {
        "answer": result.get("answer", ""),
        "answered": bool(result.get("answered", False)),
        "citations": result.get("citations", []),
        "sub_questions": result.get("sub_questions", [question]),
        "dropped": int(result.get("dropped", 0)),
        "refusal_reason": result.get("refusal_reason", ""),
    }
