import math
from typing import Dict, List, Tuple  # noqa: UP035


def cosine(a: List[float], b: List[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    da = math.sqrt(sum(x * x for x in a))
    db = math.sqrt(sum(x * x for x in b))
    if da == 0.0 or db == 0.0:
        return 0.0
    return num / (da * db)


STORE: dict[str, list[tuple[list[float], dict]]] = {}


class InMemoryVectorDB:
    def __init__(self, store: dict | None = None):
        self.store = STORE if store is None else store

    def create_collection(self, name: str):
        self.store.setdefault(name, [])

    def upsert(self, name: str, vectors: List[List[float]], payloads: List[Dict]):
        self.create_collection(name)
        self.store[name].extend(list(zip(vectors, payloads)))

    def query(self, name: str, query_vec: List[float], top_k: int = 5) -> List[Tuple[float, Dict]]:
        items = self.store.get(name, [])
        scored = [(cosine(query_vec, v), p) for v, p in items]
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_k]
