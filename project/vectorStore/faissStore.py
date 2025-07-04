# vector_store/faiss_store.py
from typing import List, Dict, Any, Sequence
import os, json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from project.documentParsers.parsers import DocumentParser

class FaissStore:
    def __init__(self,
                 dim: int = 384,
                 indexPath: str = "vectorDB/index.faiss",
                 metaPath: str  = "vectorDB/meta.json",
                 modelName: str = "intfloat/e5-small-v2"):
        self.dim = dim
        self.indexPath = indexPath
        self.metaPath = metaPath
        self.model = SentenceTransformer(modelName,device="cpu")
        self.index = None
        self.meta: List[Dict[str, Any]] = []
        self._loadIfExists()

    # ---------- public ----------
    def add(self, chunks: Sequence[str], source: str):
        vecs = self._embed(chunks)
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(vecs)
        self.meta.extend([{"text": c, "source": source} for c in chunks])
        self._persist()

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        vec = self._embed([query])
        D, I = self.index.search(vec, k)
        return [self.meta[i] for i in I[0]]

    # ---------- private ----------
    def _embed(self, texts: Sequence[str]) -> np.ndarray:
        return self.model.encode(texts, normalize_embeddings=True).astype("float32")

    def _loadIfExists(self):
        if os.path.exists(self.indexPath) and os.path.exists(self.metaPath):
            self.index = faiss.read_index(self.indexPath)
            with open(self.metaPath, "r", encoding="utf-8") as f:
                self.meta = json.load(f)

    def _persist(self):
        os.makedirs(os.path.dirname(self.indexPath), exist_ok=True)
        faiss.write_index(self.index, self.indexPath)
        with open(self.metaPath, "w", encoding="utf-8") as f:
            json.dump(self.meta, f, ensure_ascii=False, indent=2)



# Unit testing(Krni padti h bhai aap nhi samjhoge 🥲)


# if __name__ == "__main__":
    # Example usage
    # store = FaissStore()
    # text=DocumentParser().parse(r"D:\Slris\ayushResume.pdf")
    # # store.add(["This is a test chunk.", "Another chunk for testing."], "test_source")
    # store.add(text, "ayushResume.pdf")
    # print("Added documents to the vector store.")
    # results = store.search("Ayush's resume", k=1)
    # for res in results:
    #     print(res)