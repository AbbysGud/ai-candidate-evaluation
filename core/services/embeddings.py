from typing import List

try:
    from sentence_transformers import SentenceTransformer

    _MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
except Exception as e:
    _MODEL = None
    _ERR = e


class STEmbedder:
    def __init__(self):
        if _MODEL is None:
            raise RuntimeError(f"SentenceTransformer not available: {_ERR}")

    def embed(self, texts: List[str]) -> List[List[float]]:
        return _MODEL.encode(texts, normalize_embeddings=True).tolist()  # type: ignore

    def embed_query(self, text: str) -> List[float]:
        return _MODEL.encode([text], normalize_embeddings=True)[0].tolist()  # type: ignore
