import os

from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Document, ReferenceSet
from .serializers_reference import UploadReferenceSerializer
from .services.collections import ref_collection  # type: ignore
from .services.retrieval import retrieval  # type: ignore


class UploadReferenceView(APIView):

    def post(self, request):
        ser = UploadReferenceSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        ref_set = ReferenceSet.objects.get(id=ser.validated_data["reference_set_id"])  # type: ignore
        dtype = ser.validated_data["type"]  # type: ignore
        f = ser.validated_data["file"]  # type: ignore

        doc = Document.objects.create(
            type=dtype,
            ref_set=ref_set,
            filename=f.name,
            mime_type=getattr(f, "content_type", "application/octet-stream"),
            sha256_checksum="",
            storage_path="",
        )

        # --- SIMPAN VIA STORAGE (S3/GCS/Local) ---
        today = timezone.now().strftime("%Y/%m/%d")
        safe_name = os.path.basename(f.name)  # sanitasi dari backslash Windows dll
        rel_path = f"uploads/{today}/{doc.id}_{safe_name}"

        # simpan fisik ke storage backend
        storage_path = default_storage.save(rel_path, f)

        doc.storage_path = storage_path.replace("\\", "/")
        doc.save(update_fields=["storage_path"])

        collection = ref_collection(str(ref_set.id), dtype)
        retrieval.index_document(collection, doc.storage_path, doc.mime_type, str(doc.id))

        return Response(
            {
                "document_id": str(doc.id),
                "reference_set_id": str(ref_set.id),
                "collection": collection,
            },
            status=status.HTTP_201_CREATED,
        )
