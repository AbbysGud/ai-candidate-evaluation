from typing import Dict, List, Tuple

from chromadb import PersistentClient
from chromadb.config import Settings


class ChromaVectorDB:
    def __init__(self, persist_dir: str):
        self.client = PersistentClient(path=persist_dir, settings=Settings())
        self._cols: Dict[str, object] = {}

    def _get(self, name: str):
        if name not in self._cols:
            self._cols[name] = self.client.get_or_create_collection(
                name=name, metadata={"hnsw:space": "cosine"}
            )
        return self._cols[name]

    def upsert(self, collection: str, vectors: List[List[float]], payloads: List[Dict]):
        col = self._get(collection)
        ids = [p["id"] for p in payloads]
        metadatas = [
            {
                "doc_id": p.get("doc_id"),
                "offset": int(p.get("offset", 0)),
                "text": p.get("text"),
                "ts": p.get("ts"),
                "storage_path": p.get("storage_path"),
            }
            for p in payloads
        ]
        col.upsert(embeddings=vectors, metadatas=metadatas, ids=ids)  # type: ignore

    def query(self, collection: str, qv: List[float], top_k: int) -> List[Tuple[float, Dict]]:
        col = self._get(collection)
        res = col.query(query_embeddings=[qv], n_results=top_k)  # type: ignore
        out = []
        if res["ids"] and res["ids"][0]:
            for i in range(len(res["ids"][0])):
                md = res["metadatas"][0][i]
                score = 1.0 - float(res["distances"][0][i])
                out.append((score, md))
        return out

    def stats(self) -> Dict[str, int]:
        stats: Dict[str, int] = {}
        for c in self.client.list_collections():
            try:
                stats[c.name] = c.count()  # type: ignore[attr-defined]
            except Exception:
                stats[c.name] = 0
        return stats

    def delete_all(self):
        for c in list(self.client.list_collections()):
            self.client.delete_collection(c.name)
        self._cols.clear()

    def count(self, collection: str) -> int:
        col = self.client.get_or_create_collection(collection)
        return col.count()
