import hashlib

from rest_framework import serializers

from .models import Document


class UploadSerializer(serializers.Serializer):
    cv = serializers.FileField(required=True)
    report = serializers.FileField(required=True)

    def _save_doc(self, f, doc_type: str) -> Document:
        # hitung checksum
        sha = hashlib.sha256()
        for chunk in f.chunks():
            sha.update(chunk)
        checksum = sha.hexdigest()

        d = Document.objects.create(
            type=doc_type,
            filename=f.name,
            mime_type=getattr(f, "content_type", "application/octet-stream"),
            sha256_checksum=checksum,
            storage_path="",  # akan diisi setelah FileField disimpan oleh view
        )
        return d


class EvaluateSerializer(serializers.Serializer):
    job_title = serializers.CharField(max_length=200)
    cv_document_id = serializers.UUIDField()
    report_document_id = serializers.UUIDField()
    reference_set_id = serializers.UUIDField()

    def validate(self, attrs):
        cv = Document.objects.filter(id=attrs["cv_document_id"], type="cv").first()
        rp = Document.objects.filter(id=attrs["report_document_id"], type="report").first()
        if not cv or not rp:
            raise serializers.ValidationError("Documents not found or type mismatch")
        attrs["cv_doc"] = cv
        attrs["report_doc"] = rp
        return attrs
