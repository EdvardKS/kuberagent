import httpx
import asyncio
from config.settings import PICASSO_URL, CHAT_MODEL, EMBED_MODEL, VISION_MODEL
import json 


class PicassoClient:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=PICASSO_URL, timeout=60.0)
        self.semaphore = asyncio.Semaphore(5)

    async def chat_stream(self, prompt: str):
        async with self.semaphore:
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": CHAT_MODEL,
                    "prompt": prompt,
                    "stream": True
                }
            )

            async for line in response.aiter_lines():
                if not line.strip():
                    continue

                try:
                    chunk = json.loads(line)
                    yield chunk.get("response", "")
                except Exception:
                    continue
                
                
    async def chat(self, prompt: str):
        async with self.semaphore:
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": CHAT_MODEL,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    async def embed(self, text: str):
        async with self.semaphore:
            response = await self.client.post(
                "/api/embeddings",
                json={
                    "model": EMBED_MODEL,
                    "prompt": text
                }
            )
            response.raise_for_status()
            return response.json()

    async def vision(self, image_base64: str):
        async with self.semaphore:
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": VISION_MODEL,
                    "images": [image_base64],
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")


picasso = PicassoClient()