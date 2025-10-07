import logging
import os

from celery import shared_task
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone

from .models import Evaluation, Job, JobStageLog
from .services.collections import ref_collection
from .services.evaluation import run_evaluation
from .services.retrieval import retrieval
from .services.text_extractor import extract_text_auto


@shared_task(
    bind=True, max_retries=3, autoretry_for=(TimeoutError, ConnectionError), retry_backoff=True
)
def evaluate_job_task(self, job_id: str):
    with transaction.atomic():
        job = (
            Job.objects.select_for_update()
            .select_related("cv_document", "report_document", "reference_set")
            .get(id=job_id)
        )
        job.status = "processing"
        job.attempts = (job.attempts or 0) + 1
        job.started_at = timezone.now()
        job.save(update_fields=["status", "attempts", "started_at"])

        cid_jd = ref_collection(str(job.reference_set.id), "job_desc")  # type: ignore
        cid_rub = ref_collection(str(job.reference_set.id), "scoring_rubric")  # type: ignore
        cid_cb = ref_collection(str(job.reference_set.id), "case_brief")  # type: ignore

        logger = logging.getLogger(__name__)
        logger.warning(
            "[BOOT] VDB_DIR=%s exists=%s list=%s",
            settings.VDB_DIR,
            os.path.exists(settings.VDB_DIR),
            os.listdir(settings.VDB_DIR) if os.path.exists(settings.VDB_DIR) else None,
        )

        logger.warning(
            "[CHK] counts jd=%s rub=%s cb=%s",
            retrieval.count(cid_jd),
            retrieval.count(cid_rub),
            retrieval.count(cid_cb),
        )

    JobStageLog.objects.create(job=job, stage="parse_cv", status="started")
    JobStageLog.objects.create(job=job, stage="parse_report", status="started")

    def _summarize(txt: str, limit: int = 4000) -> str:
        txt = (txt or "").strip()
        return txt[:limit]

    with default_storage.open(job.cv_document.storage_path, "rb") as fcv:
        cv_text = extract_text_auto(fcv, job.cv_document.mime_type)  # type: ignore
    with default_storage.open(job.report_document.storage_path, "rb") as frp:
        report_text = extract_text_auto(frp, job.report_document.mime_type)  # type: ignore

    cv_hints = _summarize(cv_text, 4000)
    report_hints = _summarize(report_text, 4000)

    try:
        refset_id = str(job.reference_set.id or "")  # type: ignore
        prior_warn = []
        if retrieval.count(cid_jd) == 0:
            prior_warn.append("job_desc_missing")
        if retrieval.count(cid_rub) == 0:
            prior_warn.append("scoring_rubric_missing")
        if retrieval.count(cid_cb) == 0:
            prior_warn.append("case_brief_missing")

        doc_versions = f"cv={job.cv_document.id},report={job.report_document.id},refset={job.reference_set.id}"  # type: ignore

        res = run_evaluation(
            job.job_title,
            cv_hints,
            report_hints,
            refset_id,
            job_id=str(job.id),
            doc_versions=doc_versions,
            prior_warnings=",".join(prior_warn),
        )

        JobStageLog.objects.create(job=job, stage="eval_cv", status="success")
        JobStageLog.objects.create(job=job, stage="eval_project", status="success")
        JobStageLog.objects.create(
            job=job,
            stage="synthesize",
            status="success",
            details={"cv_match_rate": res["cv_match_rate"], "project_score": res["project_score"]},
        )

        Evaluation.objects.update_or_create(
            job=job,
            defaults={
                "cv_match_rate": res["cv_match_rate"],
                "cv_feedback": res["cv_feedback"],
                "project_score": res["project_score"],
                "project_feedback": res["project_feedback"],
                "overall_summary": res["overall_summary"],
                "raw_llm": res.get("raw_llm"),
            },
        )
        job.status = "completed"
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "completed_at"])

    except Exception as e:
        JobStageLog.objects.create(
            job=job, stage="synthesize", status="failed", details={"error": str(e)}
        )
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_message", "completed_at"])
        raise
