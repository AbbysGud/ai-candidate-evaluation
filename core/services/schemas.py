from pydantic import BaseModel, condecimal, validator
from typing import Optional


class CVResult(BaseModel):
    cv_match_rate: condecimal(ge=0, le=1, max_digits=3, decimal_places=2)  # type: ignore
    cv_feedback: str


class ProjectResult(BaseModel):
    project_score: condecimal(ge=1, le=5, max_digits=2, decimal_places=1)  # type: ignore
    project_feedback: str


class FinalResult(BaseModel):
    overall_summary: str


# “repair mode” helper: clamp jika tetap out-of-range
def clamp_cv(d: dict) -> CVResult:
    try:
        return CVResult(**d)
    except Exception:
        v = d.copy()
        v["cv_match_rate"] = float(max(0, min(1, float(v.get("cv_match_rate", 0)))))
        v["cv_feedback"] = v.get("cv_feedback") or ""
        return CVResult(**v)


def clamp_project(d: dict) -> ProjectResult:
    try:
        return ProjectResult(**d)
    except Exception:
        v = d.copy()
        s = float(v.get("project_score", 1))
        v["project_score"] = float(max(1, min(5, s)))
        v["project_feedback"] = v.get("project_feedback") or ""
        return ProjectResult(**v)
