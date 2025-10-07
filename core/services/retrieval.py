import logging
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone

from .chunker import simple_chunk
from .embeddings import STEmbedder
from .text_extractor import extract_text_auto
from .vectordb_chroma import ChromaVectorDB

log = logging.getLogger(__name__)

GLOBAL_EMBEDDER = STEmbedder()


def _vdb():
    return ChromaVectorDB(persist_dir=str(settings.VDB_DIR))


def _guess_mime(mime: str, storage_path: str) -> str:
    m = (mime or "").lower()
    if m and m != "application/octet-stream":
        return m
    p = (storage_path or "").lower()
    if p.endswith(".pdf"):
        return "application/pdf"
    if p.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if p.endswith(".doc"):
        return "application/msword"
    return m or "application/octet-stream"


class RetrievalService:
    def __init__(self, embedder=None):
        self.embedder = embedder or GLOBAL_EMBEDDER

    def _read_text(self, storage_path: str, mime: str) -> str:
        m2 = _guess_mime(mime, storage_path)

        try:
            with default_storage.open(storage_path, "rb") as f:
                return extract_text_auto(f, m2)
        except Exception as e:
            log.warning("[retrieval] default_storage.open failed for %s: %s", storage_path, e)

        full_path = Path(settings.MEDIA_ROOT) / storage_path
        if full_path.exists():
            return extract_text_auto(str(full_path), m2)

        log.error("[retrieval] file not found in storage or local path: %s", storage_path)
        return ""

    def index_document(self, collection: str, storage_path: str, mime: str, doc_id: str):
        text = self._read_text(storage_path, mime)
        chunks = simple_chunk(text, max_chars=800)
        if not chunks:
            log.warning("[retrieval] no chunks extracted for %s (%s)", storage_path, mime)
            return 0

        vectors = self.embedder.embed([c["text"] for c in chunks])
        payloads = []
        now = str(timezone.now())
        for i, c in enumerate(chunks):
            offset = int(c["meta"].get("offset", 0))
            chunk_id = f"{doc_id}:{i}"
            payloads.append(
                {
                    "id": chunk_id,
                    "doc_id": str(doc_id),
                    "offset": offset,
                    "text": c["text"],
                    "ts": now,
                    "storage_path": storage_path,
                }
            )

        _vdb().upsert(collection, vectors, payloads)
        return len(chunks)

    def search(self, collection: str, query: str, top_k=5) -> list[dict]:
        qv = self.embedder.embed_query(query)
        hits = _vdb().query(collection, qv, top_k=top_k)
        return [{"score": s, **p} for s, p in hits]

    def count(self, collection: str) -> int:
        return _vdb().count(collection)


retrieval = RetrievalService()
