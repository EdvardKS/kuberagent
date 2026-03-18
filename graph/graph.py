from langgraph.graph import StateGraph
from graph.state import GraphState
from graph.node import router_node, rag_node


def build_graph():
    builder = StateGraph(GraphState)

    builder.add_node("rag", rag_node)

    builder.set_entry_point("rag")
    builder.set_finish_point("rag")

    return builder.compile()


    