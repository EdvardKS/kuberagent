# KuberAgent — Arquitectura y documentación técnica

Sistema RAG (Retrieval-Augmented Generation) orquestado con LangGraph, desplegable en Kubernetes.
Combina búsqueda vectorial semántica, ingesta asíncrona y un ciclo de evaluación automática de respuestas.

---

## Estructura del proyecto

```
KuberAgent/
├── api/              # Servidor HTTP (FastAPI)
├── config/           # Variables de entorno y configuración global
├── graph/            # Grafo LangGraph: nodos, estado y ensamblado
├── ingest/           # Scripts de carga de documentos
├── k8s/              # Manifiestos Kubernetes
├── services/         # Clientes externos (LLM + vector store)
├── worker/           # Consumidor Redis para ingesta asíncrona
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Carpetas y responsabilidades

### `api/`
Punto de entrada HTTP del sistema. Expone dos endpoints:

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/chat` | POST | Ejecuta el grafo RAG con la query del usuario |
| `/ingest` | POST | Encola un documento en Redis para ingesta asíncrona |

El endpoint `/chat` invoca el grafo completo y devuelve la respuesta final al usuario.
El endpoint `/ingest` **no procesa directamente** — publica el trabajo en un Redis Stream para que el worker lo consuma.

---

### `config/`
Centraliza toda la configuración mediante variables de entorno con valores por defecto:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `PICASSO` | `http://192.168.200.134:12346` | URL del servidor de inferencia local (Ollama) |
| `CHAT_MODEL` | `llama3.1:8b` | Modelo de generación de texto |
| `EMBED_MODEL` | `nomic-embed-text` | Modelo de embeddings |
| `VISION_MODEL` | `glm-ocr` | Modelo de visión |
| `REDIS_URL` | `redis://redis:6379` | Conexión a Redis |
| `VECTOR_DB_URL` | `http://localhost:6333` | Conexión a Qdrant |

---

### `graph/`
Núcleo del sistema. Contiene el grafo LangGraph con los nodos del pipeline RAG.

- **`state.py`** — Define `GraphState`, el estado compartido entre todos los nodos
- **`node.py`** — Implementa cada nodo como función asíncrona
- **`graph.py`** — Ensambla el grafo, define aristas y el bucle de evaluación

---

### `services/`
Clientes para comunicarse con sistemas externos:

- **`client.py`** — `PicassoClient`: cliente HTTP asíncrono para el servidor Ollama. Limita concurrencia a 5 peticiones simultáneas con `asyncio.Semaphore`.
- **`vector_store.py`** — `VectorStore`: wrapper sobre Qdrant. Gestiona la colección, inserta embeddings y ejecuta búsquedas por similitud coseno.

---

### `worker/`
Proceso independiente que consume mensajes del Redis Stream `jobs`. Para cada mensaje:
1. Decodifica el texto
2. Genera el embedding con `picasso.embed()`
3. Almacena en Qdrant con `vector_store.add()`

Garantiza procesamiento exactamente una vez mediante `XACK` tras éxito.

---

### `ingest/`
Utilidad de carga inicial. Lee comandos curl de `ingesta.txt` y los envía al endpoint `/ingest` para poblar la base de conocimiento.

---

### `k8s/`
Manifiestos para despliegue en Kubernetes:
- `api-deployment.yaml` — Deployment + Service para la API
- `qdrant-deployment.yaml` — Deployment + PVC para Qdrant

---

## Diagrama de flujo completo

### Pipeline de ingesta (offline)

```
Cliente / Script
      │
      │  POST /ingest {"input": "texto..."}
      ▼
  FastAPI (api/)
      │
      │  XADD jobs {type: ingest, text: ...}
      ▼
  Redis Stream "jobs"
      │
      │  XREADGROUP (bloqueo 5s)
      ▼
  Worker (worker/)
      │
      ├─► picasso.embed(text)  ──►  Ollama (nomic-embed-text)
      │
      └─► vector_store.add(embedding, text)  ──►  Qdrant
```

---

### Pipeline RAG con evaluación (online)

```
POST /chat {"input": "¿pregunta?"}
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│                        GRAFO LANGGRAPH                          │
│                                                                 │
│  ┌──────────────┐                                               │
│  │ embed_query  │  picasso.embed(query) → vector de floats      │
│  └──────┬───────┘                                               │
│         │                                                       │
│  ┌──────▼───────┐                                               │
│  │  normalize   │  Desenvuelve dict Ollama + normalización L2   │
│  └──────┬───────┘                                               │
│         │                                                       │
│  ┌──────▼───────┐                                               │
│  │    search    │  vector_store.search(embedding, k=5)          │
│  └──────┬───────┘                                               │
│         │                                                       │
│  ┌──────▼───────┐                                               │
│  │  chunk_docs  │  Trocea docs recuperados (400 chars/chunk)    │
│  └──────┬───────┘                                               │
│         │                ┌─────────────────────┐               │
│  ┌──────▼───────┐        │  Si attempts > 0:   │               │
│  │ build_prompt │◄───────┤  prompt de reintento│               │
│  └──────┬───────┘        │  con "Intento N/3"  │               │
│         │                └─────────────────────┘               │
│  ┌──────▼───────┐                                               │
│  │   call_llm   │  picasso.chat(prompt) → respuesta             │
│  └──────┬───────┘  attempts += 1                               │
│         │                                                       │
│  ┌──────▼───────┐                                               │
│  │   evaluate   │  picasso.chat(eval_prompt) → VÁLIDA/INVÁLIDA  │
│  └──────┬───────┘                                               │
│         │                                                       │
│    ┌────┴─────┐                                                 │
│    │ ¿válida? │                                                  │
│    └──┬───┬──┘                                                  │
│  SÍ  │   │ NO (attempts < 3)                                    │
│       ▼   └──────────────► build_prompt (reintento)             │
│      END                                                        │
└─────────────────────────────────────────────────────────────────┘
      │
      ▼
response → cliente HTTP
```

---

## Estado del grafo (`GraphState`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `input` | `str` | Query original del usuario |
| `task` | `Optional[str]` | Tipo de tarea (reservado para enrutamiento futuro) |
| `query_embedding` | `Optional[List[float]]` | Vector embedding de la query |
| `raw_docs` | `Optional[List[str]]` | Documentos recuperados de Qdrant |
| `chunks` | `Optional[List[str]]` | Documentos troceados listos para el prompt |
| `context` | `Optional[str]` | Contexto ensamblado para el prompt |
| `prompt` | `Optional[str]` | Prompt completo enviado al LLM |
| `response` | `str` | Respuesta del LLM |
| `attempts` | `int` | Número de llamadas al LLM realizadas (máx 3) |
| `is_valid` | `bool` | Si la respuesta superó la evaluación |

---

## Lógica de reintento

El nodo `evaluate` envía un segundo prompt al LLM preguntando si la respuesta es **VÁLIDA** o **INVÁLIDA**.

```
is_valid = True   →  END   (se devuelve la respuesta al usuario)
is_valid = False  →  build_prompt  (se reintenta con prompt ajustado)
attempts >= 3     →  END   (se acepta la última respuesta sin importar calidad)
```

El prompt de reintento incluye el número de intento (`Intento 2/3`, `Intento 3/3`) para que el modelo sepa que debe mejorar su respuesta.

---

## Dependencias principales

| Librería | Uso |
|----------|-----|
| `fastapi` + `uvicorn` | Servidor HTTP asíncrono |
| `langgraph` | Orquestación del grafo de nodos |
| `langchain` | Utilidades LLM base |
| `qdrant-client` | Cliente para base de datos vectorial |
| `redis` | Cola de trabajos con Redis Streams |
| `httpx` | Cliente HTTP asíncrono para llamadas al LLM |
| `pydantic` | Validación de modelos de datos |

---

## Servicios en docker-compose

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| `api` | `${API_PORT}:8000` | FastAPI |
| `worker` | — | Consumidor Redis |
| `redis` | `6379` | Cola de trabajos |
| `qdrant` | `6333` | Base de datos vectorial |
