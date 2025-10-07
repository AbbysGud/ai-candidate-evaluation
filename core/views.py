from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Job
from .serializers import UploadSerializer
from .services.retrieval import retrieval  # type: ignore


class UploadBothView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        ser = UploadSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        cv_file = request.FILES["cv"]
        report_file = request.FILES["report"]

        cv_doc = ser._save_doc(cv_file, "cv")  # pyright: ignore[reportAttributeAccessIssue]
        report_doc = ser._save_doc(  # pyright: ignore[reportAttributeAccessIssue]
            report_file, "report"
        )

        today = timezone.now().strftime("%Y/%m/%d")
        cv_path = default_storage.save(f"uploads/{today}/{cv_doc.id}_{cv_file.name}", cv_file)
        report_path = default_storage.save(
            f"uploads/{today}/{report_doc.id}_{report_file.name}", report_file
        )

        cv_doc.storage_path = cv_path
        report_doc.storage_path = report_path
        cv_doc.save(update_fields=["storage_path"])
        report_doc.save(update_fields=["storage_path"])

        retrieval.index_document(
            collection="references",
            storage_path=cv_path,
            mime=cv_doc.mime_type,
            doc_id=str(cv_doc.id),
        )
        retrieval.index_document(
            collection="references",
            storage_path=report_path,
            mime=report_doc.mime_type,
            doc_id=str(report_doc.id),
        )

        return Response(
            {"cv_document_id": str(cv_doc.id), "report_document_id": str(report_doc.id)},
            status=status.HTTP_201_CREATED,
        )


class JobDetailView(APIView):
    def get(self, request, job_id):
        job = get_object_or_404(Job.objects.select_related("evaluation"), id=job_id)

        data = {
            "id": str(job.id),
            "status": job.status,
            "error_message": job.error_message,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        }

        if job.status == "completed" and getattr(job, "evaluation", None):
            ev = job.evaluation  # type: ignore
            data["evaluation"] = {
                "cv_match_rate": ev.cv_match_rate,
                "cv_feedback": ev.cv_feedback,
                "project_score": ev.project_score,
                "project_feedback": ev.project_feedback,
                "overall_summary": ev.overall_summary,
                "raw_llm": ev.raw_llm,
            }

        return Response(data, status=200)
