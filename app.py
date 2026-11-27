"""MaintiDoc — Streamlit demo: multimodal RAG and MCP ticket workflow."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from maintidoc.config import IMAGE_DIR, OLLAMA_MODEL, PROCESSED_DIR, ROOT
from maintidoc.generation import answer_question
from maintidoc.graph import run_agent
from maintidoc.mcp_calls import call_tool
from maintidoc.mcp_store import approve_ticket, prepare_ticket
from maintidoc.retrieval import Pipeline
from maintidoc.vision import DEFAULT_VISION_MODEL, describe_image

st.set_page_config(page_title="MaintiDoc SAN", page_icon="🗂️", layout="wide")
st.title("MaintiDoc · SAN Document Assistant")
st.caption(
    "Educational prototype: multimodal RAG, verifiable citations, maintenance history "
    "and tickets through MCP. No equipment control and no action without human approval."
)


@st.cache_resource(show_spinner="Loading the BGE-M3 / CLIP index…")
def get_pipeline() -> Pipeline:
    return Pipeline.load_or_build(backend="qdrant")


def show_image(path: str, caption: str) -> None:
    file = ROOT / path
    if file.is_file():
        st.image(str(file), caption=caption, width="stretch")


pipeline = get_pipeline()

with st.sidebar:
    st.header("Configuration")
    model = st.text_input("Ollama model", OLLAMA_MODEL)
    st.caption("Local model. Use qwen2.5vl:7b if installed.")
    vision_model = st.text_input("Vision model", DEFAULT_VISION_MODEL)
    use_reranker = st.checkbox("Use multilingual reranker", value=False)
    st.divider()
    st.write("**Corpus:** fictional SAN manual, 9 pages, 5 figures.")
    st.write("**Search:** BGE-M3 + CLIP + RRF.")
    st.write("**MCP:** history, tickets, human approval.")

search_tab, agent_tab, mcp_tab, corpus_tab = st.tabs(
    ["🔎 Search & answer", "🤖 LangGraph agent", "🧰 MCP tickets", "📚 Corpus"]
)

with search_tab:
    col1, col2 = st.columns([3, 2])
    with col1:
        question = st.text_area(
            "Technician question",
            value="What does the orange AL-01 LED mean?",
            height=100,
        )
    with col2:
        visual_query = st.text_input(
            "CLIP visual query (English recommended)",
            value="orange warning LED storage array front panel",
        )

    uploaded = st.file_uploader(
        "Panel photo (optional — JPG/PNG)",
        type=["jpg", "jpeg", "png", "webp"],
    )
    image_bytes = None
    if uploaded is not None:
        image_bytes = uploaded.getvalue()
        st.image(image_bytes, caption="Uploaded photo", width=420)

    if st.button("Search", type="primary"):
        image_description = None
        if image_bytes:
            with st.spinner("Analyzing the uploaded photo with the vision model…"):
                try:
                    image_description = describe_image(
                        image_bytes, model=vision_model
                    )
                    st.session_state["image_description"] = image_description
                except Exception as exc:
                    st.warning(
                        f"Vision model unavailable ({type(exc).__name__}). "
                        "Falling back to CLIP image retrieval."
                    )
                    st.session_state["image_description"] = ""
        else:
            st.session_state.pop("image_description", None)

        with st.spinner("Running text + image search and RRF fusion…"):
            st.session_state["retrieval"] = pipeline.search(
                question,
                visual_query,
                rerank=use_reranker,
                image_bytes=image_bytes,
                image_description=st.session_state.get("image_description"),
            )
            st.session_state.pop("answer", None)

    retrieval = st.session_state.get("retrieval")
    if retrieval:
        st.subheader("Pages selected after RRF fusion")
        st.dataframe(pd.DataFrame(retrieval["pages"]), hide_index=True)

        with st.expander("Supporting passages and tables", expanded=True):
            for item in retrieval["evidence"]:
                if item["type"] == "image":
                    continue
                st.markdown(
                    f"**{item['id']} — page {item['page']} — {item['type']}**"
                )
                st.code(item["content"][:1600], language=None)

        for image in retrieval["images"]:
            show_image(image["path"], f"{image['figure_id']} — page {image['page']}")

        if retrieval.get("image_description"):
            with st.expander("Vision model analysis of the uploaded photo", expanded=True):
                st.write(retrieval["image_description"])

        if st.button("Generate sourced answer"):
            with st.spinner("Running Ollama inference…"):
                st.session_state["answer"] = answer_question(
                    question,
                    retrieval,
                    model=model,
                    language="en",
                    image_description=st.session_state.get("image_description"),
                )

        answer = st.session_state.get("answer")
        if answer:
            st.subheader("Answer")
            st.write(answer.get("answer", ""))

            status_labels = {
                "answered": "Answered",
                "needs_clarification": "Needs clarification",
                "insufficient_evidence": "Insufficient evidence",
            }
            status = status_labels.get(answer.get("status"), answer.get("status"))
            st.caption(f"Status: **{status}** · mode: **{answer.get('mode')}**")

            issues = answer.get("issues") or []
            if issues:
                st.warning("Citation check: " + "; ".join(issues))
            else:
                st.success("Citation check: all references exist in the retrieved evidence.")

            for citation in answer.get("citations", []):
                st.success(f"{citation.get('id')} · page {citation.get('page')}")

            for uncertainty in answer.get("uncertainties", []):
                st.warning(uncertainty)

            with st.expander("Raw model response"):
                st.code(answer.get("raw", ""), language="json")

with agent_tab:
    st.subheader("LangGraph agent")
    st.caption(
        "Workflow: retrieve → generate → validate citations → answer or clarification."
    )
    agent_question = st.text_area(
        "Agent question",
        value="What does the orange AL-01 LED mean?",
        height=90,
    )
    agent_visual_query = st.text_input(
        "Agent CLIP visual query",
        value="orange warning LED storage array front panel",
    )
    if st.button("Run LangGraph agent"):
        with st.spinner("Running retrieve → generate → validate…"):
            st.session_state["agent_result"] = run_agent(
                agent_question,
                agent_visual_query,
                model=model,
                language="en",
                pipeline=pipeline,
            )

    agent_result = st.session_state.get("agent_result")
    if agent_result:
        agent_answer = agent_result.get("answer", {})
        st.write(agent_answer.get("answer", ""))
        st.caption(
            f"Status: **{agent_answer.get('status')}** · "
            f"nodes: retrieve → generate → validate"
        )
        for citation in agent_answer.get("citations", []):
            st.success(f"{citation.get('id')} · page {citation.get('page')}")
        for uncertainty in agent_answer.get("uncertainties", []):
            st.warning(uncertainty)

        retrieval = agent_result.get("retrieval", {})
        if retrieval:
            st.subheader("Evidence used by the agent")
            st.dataframe(pd.DataFrame(retrieval.get("pages", [])), hide_index=True)

            with st.expander("Passages and tables sent to the model", expanded=True):
                for item in retrieval.get("evidence", []):
                    if item["type"] == "image":
                        continue
                    st.markdown(
                        f"**{item['id']} — page {item['page']} — {item['type']}**"
                    )
                    st.code(item["content"][:1600], language=None)

            for image in retrieval.get("images", []):
                show_image(image["path"], f"{image['figure_id']} — page {image['page']}")

with mcp_tab:
    st.subheader("Maintenance history and tickets through MCP")
    equipment_id = st.text_input("Equipment ID", value="SAN-LAB-2000")

    if st.button("Fetch history"):
        st.session_state["history"] = call_tool(
            "get_equipment_history", {"equipment_id": equipment_id}
        )
        st.session_state["open_tickets"] = call_tool(
            "get_open_tickets", {"equipment_id": equipment_id}
        )

    history = st.session_state.get("history")
    if history:
        st.write("**Interventions**")
        st.dataframe(pd.DataFrame(history.get("entries", [])), hide_index=True)
        st.write("**Open tickets**")
        st.dataframe(
            pd.DataFrame(st.session_state.get("open_tickets", {}).get("entries", [])),
            hide_index=True,
        )

    st.divider()
    st.subheader("Prepare a ticket")
    with st.form("ticket_form"):
        title = st.text_input("Title", value="AL-01 alert on fabric A")
        description = st.text_area(
            "Description",
            value=(
                "FC path degraded on HBA1, recurrence to be checked. "
                "Evidence: ALARM-TAB-01, FIG-02, INC-104."
            ),
        )
        prepared = st.form_submit_button("Prepare draft")

    if prepared:
        st.session_state["draft"] = prepare_ticket(
            equipment_id, title, description
        )["draft"]
        st.session_state.pop("approval", None)

    draft = st.session_state.get("draft")
    if draft:
        st.info(
            f"Draft **{draft['draft_id']}** — no ticket has been created yet."
        )
        st.json(draft["content"])

        if st.button("Approve this draft (human)"):
            st.session_state["approval"] = approve_ticket(draft["draft_id"])

        approval = st.session_state.get("approval")
        if approval:
            st.success(f"Approval token: `{approval['approval_token']}`")

            if st.button("Create ticket via MCP"):
                result = call_tool(
                    "create_ticket",
                    {
                        "equipment_id": equipment_id,
                        "title": draft["content"]["title"],
                        "description": draft["content"]["description"],
                        "approval_token": approval["approval_token"],
                        "idempotency_key": draft["draft_id"],
                    },
                )
                st.json(result)

with corpus_tab:
    st.subheader("Corpus inventory")
    inventory = pd.read_csv(PROCESSED_DIR / "inventory.csv")
    st.dataframe(inventory, hide_index=True)

    col_pages, col_tables, col_figures = st.columns(3)
    col_pages.metric("Pages", 9)
    col_tables.metric("Tables", 9)
    col_figures.metric("Figures", 5)

    st.subheader("Extracted figures")
    columns = st.columns(3)
    for index, image in enumerate(sorted(IMAGE_DIR.glob("fig*.png"))):
        with columns[index % 3]:
            st.image(str(image), caption=image.name, width="stretch")

st.divider()
st.caption(
    "Limitations: fictional corpus, citations checked structurally but not yet "
    "semantically, local model behaviour varies, no action on real equipment."
)
