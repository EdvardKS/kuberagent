from fastapi import FastAPI
from fastapi.responses import StreamingResponse
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

# @app.post("/chat/stream")
# async def chat_stream(req: ChatRequest):
#     async def generator():
#         async for chunk in picasso.chat_stream(req.input):
#             yield chunk
#     return StreamingResponse(generator(), media_type="text/plain")

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


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )