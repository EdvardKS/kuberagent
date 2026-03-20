import redis 
import uvicorn
from fastapi import FastAPI 
from pydantic import BaseModel
from graph.graph import build_graph
from services.client import picasso
from config.settings import REDIS_URL, Colors
from services.vector_store import vector_store
from fastapi.responses import PlainTextResponse
 

r = redis.Redis.from_url(REDIS_URL)
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

    colored = f"\n{Colors.BLUE}{result['response']}{Colors.RESET}\n"
    print(colored)
    return colored

@app.post("/ingest")
async def ingest(req: ChatRequest):
    job = {
        "type": "ingest",
        "text": req.input
    }

    r.xadd("jobs", job)

    return {"status": "queued"}

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )