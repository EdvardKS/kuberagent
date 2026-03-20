import redis
import asyncio
from services.client import picasso
from config.settings import REDIS_URL
from services.vector_store import vector_store 

r = redis.Redis.from_url(REDIS_URL)

STREAM = "jobs"
GROUP = "workers"
CONSUMER = "worker-1"

def setup():
    try:
        r.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
    except:
        pass

async def process(message):
    data = message[1]
    text = data[b"text"].decode()

    emb = await picasso.embed(text)
    vector_store.add(emb, text)

async def main():
    setup()

    while True:
        messages = r.xreadgroup(
            GROUP,
            CONSUMER,
            {STREAM: ">"},
            count=1,
            block=5000
        )

        for stream, msgs in messages:
            for msg in msgs:
                msg_id = msg[0]

                try:
                    await process(msg)
                    r.xack(STREAM, GROUP, msg_id)
                except Exception as e:
                    print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())