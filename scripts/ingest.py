import asyncio
from services.client import picasso
from services.vector_store import vector_store

documents = [
    "LangGraph es una librería para orquestar agentes. Desarrollado por khachatryan",
    "Kubernetes sirve para orquestar contenedores.",
    "RAG combina recuperación de información con generación."
]


async def main():
    for doc in documents:
        emb = await picasso.embed(doc)
        vector_store.add(emb, doc)

    print("Documentos indexados")


if __name__ == "__main__":
    asyncio.run(main())