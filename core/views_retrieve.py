from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Document

from .services.retrieval import retrieval


class RetrieveView(APIView):
    def get(self, request):
        q = request.query_params.get("query", "") or ""
        collection = request.query_params.get("collection", "references") or "references"
        try:
            top_k = int(request.query_params.get("top_k", 5))
        except Exception:
            top_k = 5

        hits = retrieval.search(collection, q, top_k=top_k) if q else []
        return Response({"collection": collection, "query": q, "hits": hits})


class IndexStatsView(APIView):
    def get(self, request):
        stats = retrieval.vdb.stats()
        return Response({"collections": stats})


class ReindexAllView(APIView):
    def post(self, request):
        collection = request.data.get("collection", "references")

        reindexed_docs = 0
        skipped_docs = 0
        failed_docs = 0
        errors = []

        def _is_file(path_str: str) -> bool:
            if not path_str:
                return False
            try:
                if default_storage.exists(path_str):
                    pass
            except Exception:
                pass

            p = Path(path_str)
            if p.is_absolute():
                return p.is_file()

            local = Path(settings.MEDIA_ROOT) / path_str
            return local.is_file()

        def _normalize(path_str: str) -> str:
            return path_str or ""

        for d in Document.objects.all().only("id", "storage_path", "mime_type"):
            try:
                sp = _normalize(d.storage_path)

                if not sp or sp.endswith("/") or not _is_file(sp):
                    skipped_docs += 1
                    continue

                count_chunks = retrieval.index_document(collection, sp, d.mime_type, str(d.id))
                if count_chunks > 0:
                    reindexed_docs += 1
                else:
                    skipped_docs += 1

            except Exception as e:
                failed_docs += 1
                errors.append(
                    {
                        "doc_id": str(d.id),
                        "storage_path": d.storage_path,
                        "error": str(e)[:500],
                    }
                )

        stats = retrieval.vdb.stats()
        return Response(
            {
                "collection": collection,
                "reindexed_docs": reindexed_docs,
                "skipped_docs": skipped_docs,
                "failed_docs": failed_docs,
                "errors": errors[:10],
                "collections": stats,
            }
        )
