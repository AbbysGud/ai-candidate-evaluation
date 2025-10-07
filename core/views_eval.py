from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import IdempotencyKey, Job
from .serializers import EvaluateSerializer
from .tasks import evaluate_job_task


class EvaluateNowView(APIView):
    def post(self, request):
        ser = EvaluateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        reference_set_id = str(ser.validated_data["reference_set_id"])  # type: ignore

        key = request.headers.get("Idempotency-Key")
        if key:
            existing = IdempotencyKey.objects.select_related("job").filter(key=key).first()
            if existing:
                return Response(
                    {"id": str(existing.job.id), "status": existing.job.status},
                    status=status.HTTP_202_ACCEPTED,
                )

        job = Job.objects.create(
            cv_document=ser.validated_data["cv_doc"],  # type: ignore
            report_document=ser.validated_data["report_doc"],  # type: ignore
            job_title=ser.validated_data["job_title"],  # type: ignore
            status="queued",
            reference_set_id=reference_set_id,
        )

        if key:
            IdempotencyKey.objects.create(key=key, job=job)

        evaluate_job_task.delay(str(job.id))  # type: ignore

        return Response({"id": str(job.id), "status": "queued"}, status=status.HTTP_202_ACCEPTED)
