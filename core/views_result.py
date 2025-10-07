from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Evaluation, Job


class ResultView(APIView):
    def get(self, request, job_id: str):
        job = Job.objects.filter(id=job_id).first()
        if not job:
            return Response({"detail": "job not found"}, status=404)
        if job.status in ["queued", "processing"]:
            return Response({"id": str(job.id), "status": job.status})
        if job.status == "failed":
            return Response(
                {
                    "id": str(job.id),
                    "status": "failed",
                    "error_code": job.error_code,
                    "error_message": job.error_message,
                }
            )
        # completed
        ev = getattr(job, "evaluation", None)
        if not ev:
            return Response({"id": str(job.id), "status": "processing"})
        return Response(
            {
                "id": str(job.id),
                "status": "completed",
                "result": {
                    "cv_match_rate": ev.cv_match_rate,
                    "cv_feedback": ev.cv_feedback,
                    "project_score": ev.project_score,
                    "project_feedback": ev.project_feedback,
                    "overall_summary": ev.overall_summary,
                },
            }
        )
