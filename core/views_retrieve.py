from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Document

from .services.retrieval import retrieval


class RetrieveView(APIView):
    def get(self, request):
        q = request.query_params.get("query", "")
        collection = request.query_params.get("collection", "references")
        hits = retrieval.search("references", q, top_k=5) if q else []
        return Response({"collection": collection, "query": q, "hits": hits})


class IndexStatsView(APIView):
    def get(self, request):
        stats = retrieval.vdb.stats()
        return Response({"collections": stats})


class ReindexAllView(APIView):
    def post(self, request):
        cnt = 0
        for d in Document.objects.all():
            retrieval.index_document("references", d.storage_path, d.mime_type, str(d.id))
            cnt += 1
        stats = retrieval.vdb.stats()
        return Response({"reindexed_docs": cnt, "collections": stats})
