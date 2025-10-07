import uuid

from django.db import models


class Candidate(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"


class ReferenceSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)  # e.g., "Backend Engineer - Oct 2025"
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Document(models.Model):
    DOC_TYPES = [
        ("cv", "CV"),
        ("report", "Project Report"),
        ("job_desc", "Job Description"),
        ("case_brief", "Case Study Brief"),
        ("scoring_rubric", "Scoring Rubric"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=20, choices=DOC_TYPES, default="cv")
    filename = models.CharField(max_length=255, default="")
    mime_type = models.CharField(max_length=100, default="")
    sha256_checksum = models.CharField(max_length=64, db_index=True, default="")
    storage_path = models.CharField(max_length=512, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    ref_set = models.ForeignKey(
        ReferenceSet, null=True, blank=True, on_delete=models.SET_NULL, related_name="documents"
    )


class DocumentText(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="texts")
    page_number = models.PositiveIntegerField()
    content = models.TextField()


class Job(models.Model):
    STATUS = [
        ("queued", "queued"),
        ("processing", "processing"),
        ("completed", "completed"),
        ("failed", "failed"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv_document = models.ForeignKey(Document, on_delete=models.PROTECT, related_name="jobs_as_cv")
    report_document = models.ForeignKey(
        Document, on_delete=models.PROTECT, related_name="jobs_as_report"
    )
    job_title = models.CharField(max_length=200)
    status = models.CharField(max_length=12, choices=STATUS, default="queued")
    attempts = models.PositiveSmallIntegerField(default=0)
    error_code = models.CharField(max_length=64, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    reference_set = models.ForeignKey(
        ReferenceSet, null=True, blank=True, on_delete=models.SET_NULL, related_name="jobs"
    )


class JobStageLog(models.Model):
    STAGES = [
        ("parse_cv", "parse_cv"),
        ("eval_cv", "eval_cv"),
        ("parse_report", "parse_report"),
        ("eval_project", "eval_project"),
        ("synthesize", "synthesize"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="stage_logs")
    stage = models.CharField(max_length=20, choices=STAGES)
    status = models.CharField(max_length=20)  # started/success/failed
    details = models.JSONField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)


class Evaluation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name="evaluation")
    cv_match_rate = models.FloatField(null=True, blank=True)
    cv_feedback = models.TextField(null=True, blank=True)
    project_score = models.FloatField(null=True, blank=True)
    project_feedback = models.TextField(null=True, blank=True)
    overall_summary = models.TextField(null=True, blank=True)
    raw_llm = models.JSONField(null=True, blank=True)


class IdempotencyKey(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="idempotency_keys")
    created_at = models.DateTimeField(auto_now_add=True)
