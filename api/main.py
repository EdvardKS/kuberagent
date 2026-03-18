from fastapi import FastAPI 
from services.vector_store import vector_store
from services.client import picasso
from pydantic import BaseModel
import uvicorn
from graph.graph import build_graph
from fastapi.responses import PlainTextResponse
from config.settings import Colors

app = FastAPI(title="LangGraph API")

graph = build_graph()


class ChatRequest(BaseModel):
    input: str


@app.get("/")
async def health():
    return {"status": "ok"} 

@app.post("/chat", response_class=PlainTextResponse)
async def chat(req: ChatRequest):
    result = await graph.ainvoke({
        "input": req.input,
        "task": None,
        "response": ""
    })

    colored = f"{Colors.BLUE}{result['response']}{Colors.RESET}"
    print(colored)
    return colored

    return result

@app.post("/ingest")
async def ingest(req: ChatRequest):
    doc = req.input

    emb = await picasso.embed(doc)

    vector_store.add(emb, doc)

    return {"status": "ok", "doc": doc[:50]}

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )