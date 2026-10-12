from langgraph.graph import StateGraph, START, END
from ..schemas import AgentState
from ..nodes import (
    memory_load_node,
    InputGuardrailNode,
    intent_classification,
    query_rewrite,
    risk_profiler_node,
    market_data_node,
    news_node,
    sentiment_node,
    calculator_node,
    generator_node,
    verification_node,
    fallback_node,
    output_guardrails_node,
    memory_save_node,
)


def guardrail_route(state: AgentState) -> str:
    return "blocked" if state.get("blocked") else "safe"


def data_route(state: AgentState) -> str:
    """Where to go after query_rewriter + risk_profiler."""
    intent = state.get("intent")
    if intent in ("live_data", "multi_step"):
        return "market"
    if intent == "document":
        return "news"          # RAG skipped → at least pull news
    return "generate"          # conceptual → straight to LLM


def verify_route(state: AgentState) -> str:
    v = state.get("verification") or {}
    attempts = state.get("attempts", 0)
    if v.get("ok") or attempts >= 2:
        return "ok"
    return "retry"


def build_graph():
    g = StateGraph(AgentState)

    # --- nodes ---
    g.add_node("memory_load", memory_load_node)
    g.add_node("input_guardrails", InputGuardrailNode)
    g.add_node("intent", intent_classification)
    g.add_node("query_rewriter", query_rewrite)
    g.add_node("risk_profiler", risk_profiler_node)

    g.add_node("market_data", market_data_node)
    g.add_node("news", news_node)
    g.add_node("sentiment", sentiment_node)
    g.add_node("calculator", calculator_node)

    g.add_node("generate", generator_node)
    g.add_node("verify", verification_node)
    g.add_node("fallback", fallback_node)
    g.add_node("output_guardrails", output_guardrails_node)
    g.add_node("memory_save", memory_save_node)

    # --- wiring ---
    g.add_edge(START, "memory_load")
    g.add_edge("memory_load", "input_guardrails")

    g.add_conditional_edges(
        "input_guardrails",
        guardrail_route,
        {"blocked": END, "safe": "intent"},
    )
    g.add_edge("intent", "query_rewriter")
    g.add_edge("query_rewriter", "risk_profiler")

    g.add_conditional_edges(
        "risk_profiler",
        data_route,
        {"market": "market_data", "news": "news", "generate": "generate"},
    )

    g.add_edge("market_data", "news")
    g.add_edge("news", "sentiment")
    g.add_edge("sentiment", "calculator")
    g.add_edge("calculator", "generate")

    g.add_edge("generate", "verify")
    g.add_conditional_edges(
        "verify", verify_route, {"ok": "output_guardrails", "retry": "fallback"}
    )
    g.add_edge("fallback", "generate")
    g.add_edge("output_guardrails", "memory_save")
    g.add_edge("memory_save", END)

    return g.compile()


graph = build_graph() 

png_image = graph.get_graph().draw_mermaid_png()
with open("Graph_dig.png","wb") as f: 
    f.write(png_image) 

    