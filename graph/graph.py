from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.node import (
    embed_query_node,
    normalize_node,
    search_node,
    chunk_docs_node,
    build_prompt_node,
    call_llm_node,
    evaluate_node,
    should_retry,
)


def build_graph():
    builder = StateGraph(GraphState)

    builder.add_node("embed_query", embed_query_node)
    builder.add_node("normalize", normalize_node)
    builder.add_node("search", search_node)
    builder.add_node("chunk_docs", chunk_docs_node)
    builder.add_node("build_prompt", build_prompt_node)
    builder.add_node("call_llm", call_llm_node)
    builder.add_node("evaluate", evaluate_node)

    builder.set_entry_point("embed_query")
    builder.add_edge("embed_query", "normalize")
    builder.add_edge("normalize", "search")
    builder.add_edge("search", "chunk_docs")
    builder.add_edge("chunk_docs", "build_prompt")
    builder.add_edge("build_prompt", "call_llm")
    builder.add_edge("call_llm", "evaluate")

    builder.add_conditional_edges(
        "evaluate",
        should_retry,
        {
            "end": END,
            "retry": "build_prompt",
        },
    )

    return builder.compile()
