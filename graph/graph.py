from langgraph.graph import StateGraph
from graph.state import GraphState
from graph.node import router_node, chat_node, embed_node, vision_node


def build_graph():
    builder = StateGraph(GraphState)

    # nodos
    builder.add_node("router", router_node)
    builder.add_node("chat", chat_node)
    builder.add_node("embed", embed_node)
    builder.add_node("vision", vision_node)

    # entrada
    builder.set_entry_point("router")

    # branching
    builder.add_conditional_edges(
        "router",
        lambda state: state["task"],
        {
            "chat": "chat",
            "embed": "embed",
            "vision": "vision",
        }
    )

    # finales
    builder.set_finish_point("chat")
    builder.set_finish_point("embed")
    builder.set_finish_point("vision")

    return builder.compile()


    