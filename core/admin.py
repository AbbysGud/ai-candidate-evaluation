from django.contrib import admin

from .models import Candidate, Document, Evaluation, IdempotencyKey, Job, JobStageLog

admin.site.register(Candidate)
admin.site.register(Document)
admin.site.register(Evaluation)
admin.site.register(Job)
admin.site.register(JobStageLog)
admin.site.register(IdempotencyKey)
