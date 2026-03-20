import os

PICASSO_URL = os.getenv("PICASSO", "http://192.168.200.134:12346")

CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.1:8b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
VISION_MODEL = os.getenv("VISION_MODEL", "glm-ocr")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
VECTOR_DB_URL = os.getenv("VECTOR_DB_URL", "http://localhost:6333")

# Colores ANSI
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"