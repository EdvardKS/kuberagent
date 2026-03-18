from services.client import picasso
from graph.state import GraphState


# 🔹 Router
async def router_node(state: GraphState) -> GraphState:
    text = state["input"].lower()

    if "imagen" in text or "ocr" in text:
        task = "vision"
    elif "embedding" in text:
        task = "embed"
    else:
        task = "chat"

    return {**state, "task": task}


# 🔹 Chat
async def chat_node(state: GraphState) -> GraphState:
    result = await picasso.chat(state["input"])

    return {**state, "response": result}


# 🔹 Embedding
async def embed_node(state: GraphState) -> GraphState:
    result = await picasso.embed(state["input"])

    return {**state, "response": str(result)}


# 🔹 Vision
async def vision_node(state: GraphState) -> GraphState:
    # aquí deberías pasar imagen real (base64)
    result = await picasso.vision(state["input"])

    return {**state, "response": result}