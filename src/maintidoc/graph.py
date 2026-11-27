"""Workflow agentique LangGraph : retrieval → génération → validation → clarification."""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, StateGraph

from .generation import answer_question
from .retrieval import Pipeline


class AgentState(TypedDict, total=False):
    question: str
    visual_query: str
    retrieval: dict
    answer: dict
    route: str


def _clarification(state: AgentState, language: str) -> dict:
    if language == "en":
        message = (
            "I cannot support a reliable answer with the retrieved evidence. "
            "Please provide the exact alarm code, the equipment model, or a sharper photo of the panel."
        )
    else:
        message = (
            "Je ne peux pas soutenir une réponse fiable avec les preuves récupérées. "
            "Précisez le code d'alarme, le modèle de l'équipement ou fournissez une photo plus nette du panneau."
        )
    return {
        "status": "needs_clarification",
        "answer": message,
        "citations": [],
        "uncertainties": ["Preuves insuffisantes ou ambiguës."],
        "mode": "langgraph",
    }


def build_graph(pipeline: Pipeline, model: str, language: str = "fr"):
    def retrieve(state: AgentState) -> dict:
        retrieval = pipeline.search(
            state["question"], state.get("visual_query"), rerank=False
        )
        return {"retrieval": retrieval}

    def generate(state: AgentState) -> dict:
        answer = answer_question(
            state["question"], state["retrieval"], model=model, language=language
        )
        answer["mode"] = "langgraph"
        return {"answer": answer}

    def route(state: AgentState) -> str:
        answer = state.get("answer", {})
        if answer.get("status") == "answered" and answer.get("citations"):
            return "finalize"
        return "clarify"

    def finalize(state: AgentState) -> dict:
        return {}

    def clarify(state: AgentState) -> dict:
        return {"answer": _clarification(state, language)}

    graph = StateGraph(AgentState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_node("finalize", finalize)
    graph.add_node("clarify", clarify)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_conditional_edges(
        "generate", route, {"finalize": "finalize", "clarify": "clarify"}
    )
    graph.add_edge("finalize", END)
    graph.add_edge("clarify", END)
    return graph.compile()


def run_agent(question: str, visual_query: str = "", model: str = "llama3.2:latest",
              language: str = "fr", pipeline: Pipeline | None = None) -> dict:
    owned = pipeline is None
    pipeline = pipeline or Pipeline.load_or_build(backend="qdrant")
    try:
        agent = build_graph(pipeline, model=model, language=language)
        state = agent.invoke({"question": question, "visual_query": visual_query})
        return state
    finally:
        if owned:
            pipeline.close()


if __name__ == "__main__":
    result = run_agent(
        "What does the orange AL-01 LED mean?",
        "orange warning LED storage array front panel",
        language="en",
    )
    print(result["answer"]["status"])
    print(result["answer"]["answer"])
    print(result["answer"].get("citations"))
