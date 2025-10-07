from rest_framework import serializers

from .models import Document


class UploadReferenceSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=[
            "job_desc",
            "case_brief",
            "scoring_rubric",
        ]
    )
    reference_set_id = serializers.UUIDField(required=True)
    file = serializers.FileField()

    def create(self, validated_data):
        f = validated_data["file"]
        doc = Document.objects.create(
            type=validated_data["type"],
            filename=f.name,
            mime_type=f.content_type or "application/octet-stream",
            sha256_checksum="",
            storage_path="",
        )
        return doc
