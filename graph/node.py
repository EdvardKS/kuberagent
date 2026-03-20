from services.client import picasso
from services.vector_store import vector_store
from graph.state import GraphState


# ── 1. Embed query ──────────────────────────────────────────────────────────
async def embed_query_node(state: GraphState) -> GraphState:
    embedding = await picasso.embed(state["input"])
    return {**state, "query_embedding": embedding, "attempts": 0, "is_valid": False}


# ── 2. Normalize ────────────────────────────────────────────────────────────
async def normalize_node(state: GraphState) -> GraphState:
    embedding = state["query_embedding"]

    # Desenvuelve formato dict de Ollama {"embedding": [...]}
    if isinstance(embedding, dict):
        embedding = embedding.get("embedding", [])

    # Normalización L2
    norm = sum(x ** 2 for x in embedding) ** 0.5 # type: ignore
    if norm > 0:
        embedding = [x / norm for x in embedding] # type: ignore

    return {**state, "query_embedding": embedding}


# ── 3. Search ───────────────────────────────────────────────────────────────
async def search_node(state: GraphState) -> GraphState:
    docs = vector_store.search(embedding=state["query_embedding"], k=5)
    return {**state, "raw_docs": docs}


# ── 4. Chunk docs ───────────────────────────────────────────────────────────
async def chunk_docs_node(state: GraphState) -> GraphState:
    docs = state.get("raw_docs") or []
    chunk_size = 400
    chunks = []

    for doc in docs:
        for i in range(0, len(doc), chunk_size):
            piece = doc[i : i + chunk_size].strip()
            if piece:
                chunks.append(piece)

    return {**state, "chunks": chunks}


# ── 5. Build prompt ─────────────────────────────────────────────────────────
async def build_prompt_node(state: GraphState) -> GraphState:
    query = state["input"]
    chunks = state.get("chunks") or []
    attempts = state.get("attempts", 0)

    context = "\n\n".join(chunks) if chunks else "No hay contexto disponible."

    if attempts == 0:
        prompt = f"""Responde a la pregunta usando ÚNICAMENTE el contexto proporcionado.

Reglas:
- Extrae información explícita del contexto
- Si la información aparece varias veces, unifícala
- Si el contexto contiene el dato, debes responderlo
- NO digas "no lo sé" si la información está presente
- Responde de forma clara, directa y completa

Contexto:
{context}

Pregunta:
{query}

Respuesta:"""
    else:
        prompt = f"""Intento {attempts + 1}/3. La respuesta anterior fue insuficiente.
Proporciona una respuesta más completa, detallada y precisa.

Contexto:
{context}

Pregunta:
{query}

Respuesta detallada:"""

    return {**state, "context": context, "prompt": prompt}


# ── 6. Call LLM ─────────────────────────────────────────────────────────────
async def call_llm_node(state: GraphState) -> GraphState:
    result = await picasso.chat(state["prompt"]) # type: ignore
    return {**state, "response": result, "attempts": state.get("attempts", 0) + 1}


# ── 7. Evaluate ─────────────────────────────────────────────────────────────
async def evaluate_node(state: GraphState) -> GraphState:
    attempts = state.get("attempts", 1)

    # Si ya agotamos los 3 intentos, aceptamos lo que hay
    if attempts >= 3:
        return {**state, "is_valid": True}

    eval_prompt = f"""Evalúa si la siguiente respuesta contesta adecuadamente la pregunta.

Pregunta: {state["input"]}

Respuesta: {state["response"]}

Responde ÚNICAMENTE con "VÁLIDA" si la respuesta es completa y relevante,
o "INVÁLIDA" si es vaga, incompleta o no responde la pregunta."""

    evaluation = await picasso.chat(eval_prompt)
    is_valid = "VÁLIDA" in evaluation.upper()

    return {**state, "is_valid": is_valid}


# ── Conditional edge ─────────────────────────────────────────────────────────
def should_retry(state: GraphState) -> str:
    if state.get("is_valid", False):
        return "end"
    return "retry"
