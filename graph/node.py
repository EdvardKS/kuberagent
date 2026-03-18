from services.client import picasso
from services.vector_store import vector_store
from graph.state import GraphState


# 🔹 Router
async def router_node(state: GraphState) -> GraphState:
    return {**state, "task": "rag"}  # forzamos RAG ahora


# 🔹 RAG node
async def rag_node(state: GraphState) -> GraphState:
    query = state["input"]

    query_embedding = await picasso.embed(query)

    docs = vector_store.search(query_embedding)

    context = "\n".join(docs)

    prompt = f"""
Responde usando SOLO el contexto.
Si no está, di "No lo sé".

Contexto:
{context}

Pregunta:
{query}
"""

    result = await picasso.chat(prompt)

    return {**state, "response": result}

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
