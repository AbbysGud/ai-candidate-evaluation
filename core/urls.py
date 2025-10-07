from django.urls import path

from .views import UploadBothView, health, JobDetailView
from .views_eval import EvaluateNowView
from .views_reference import UploadReferenceView
from .views_reference_set import ReferenceSetView
from .views_result import ResultView
from .views_retrieve import IndexStatsView, ReindexAllView, RetrieveView

urlpatterns = [
    path("health/", health, name="health"),
    path("upload/", UploadBothView.as_view(), name="upload-both"),
    path("upload-reference/", UploadReferenceView.as_view(), name="upload-reference"),
    path("evaluate", EvaluateNowView.as_view(), name="evaluate"),
    path("result/<uuid:job_id>", ResultView.as_view(), name="result"),
    path("retrieve", RetrieveView.as_view(), name="retrieve"),
    path("reference-set", ReferenceSetView.as_view()),
    path("debug/index-stats", IndexStatsView.as_view(), name="index-stats"),
    path("debug/reindex-all", ReindexAllView.as_view(), name="reindex-all"),
    path("jobs/<uuid:job_id>", JobDetailView.as_view()),
]
