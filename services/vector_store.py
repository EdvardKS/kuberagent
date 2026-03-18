import faiss
import numpy as np
import pickle
import os


class VectorStore:
    def __init__(self, path="output"):
        self.path = path
        self.index = None
        self.texts = []

        os.makedirs(self.path, exist_ok=True)
        self._load()

    def _normalize(self, embedding):
        if isinstance(embedding, dict):
            embedding = embedding.get("embedding", [])
        return np.array(embedding, dtype="float32")

    def add(self, embedding, text):
        vec = self._normalize(embedding)

        if vec.ndim == 1:
            vec = np.expand_dims(vec, axis=0)

        if self.index is None:
            self.index = faiss.IndexFlatL2(vec.shape[1])

        self.index.add(vec) # type: ignore
        self.texts.append(text)

    def search(self, embedding, k=3):
        if self.index is None or len(self.texts) == 0:
            return []

        k = min(k, len(self.texts))

        vec = self._normalize(embedding)

        if vec.ndim == 1:
            vec = np.expand_dims(vec, axis=0)

        D, I = self.index.search(vec, k) # type: ignore

        return [self.texts[i] for i in I[0] if 0 <= i < len(self.texts)]

    def save(self):
        if self.index is not None:
            faiss.write_index(self.index, os.path.join(self.path, "faiss.index"))

        with open(os.path.join(self.path, "texts.pkl"), "wb") as f:
            pickle.dump(self.texts, f)

    def _load(self):
        index_path = os.path.join(self.path, "faiss.index")
        texts_path = os.path.join(self.path, "texts.pkl")

        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)

        if os.path.exists(texts_path):
            with open(texts_path, "rb") as f:
                self.texts = pickle.load(f)


vector_store = VectorStore()