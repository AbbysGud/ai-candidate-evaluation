import json
from collections import defaultdict
from typing import Any, Dict, List  # noqa: UP035

from .llm_client import LLMClient
from .prompts import CV_PROMPT, FINAL_PROMPT, PROJECT_PROMPT
from .rag import fetch_cv_context, fetch_project_context
from .schemas import FinalResult, clamp_cv, clamp_project

PROJECT_BUCKETS = {
    "correctness": (
        ["prompt", "chain", "rag", "retrieval", "embedding", "context", "grounding"],
        0.30,
    ),
    "quality": (["modular", "clean", "refactor", "test", "pytest", "rspec", "coverage"], 0.25),
    "resilience": (
        ["retry", "backoff", "timeout", "idempotency", "circuit", "worker", "async", "queue"],
        0.20,
    ),
    "docs": (["readme", "setup", "instruction", "trade-off", "explain", "design"], 0.15),
    "creativity": (["bonus", "extra", "improve", "enhancement"], 0.10),
}


def _score_buckets(texts: List[str], buckets: Dict[str, tuple[list[str], float]], scale5: bool):
    text = " ".join(texts).lower()
    total = 0.0
    for _, (keys, w) in buckets.items():
        present = sum(1 for k in keys if k in text)
        ratio = present / max(1, len(keys))
        score5 = 1 + ratio * 4
        total += (score5 if scale5 else ratio) * w
    return total


llm = LLMClient()


def _safe_format(tmpl: str, mapping: Dict[str, Any]) -> str:
    d = defaultdict(str, **mapping)
    return tmpl.format_map(d)


def run_evaluation(
    job_title: str,
    cv_hints: str,
    report_hints: str,
    reference_set_id: str,
    job_id: str = "",
    doc_versions: str = "",
    prior_warnings: str = "",
):
    job_desc, cv_rubric = fetch_cv_context(job_title, reference_set_id)
    case_brief, project_rubric = fetch_project_context(reference_set_id)

    baseline_proj = _score_buckets([report_hints], PROJECT_BUCKETS, scale5=True)
    baseline_proj = max(1.0, min(5.0, round(baseline_proj, 1)))

    job_desc_short = (job_desc or "").strip()[:400]

    base_vars = {
        "job_title": job_title,
        "job_id": job_id,
        "doc_versions": doc_versions,
        "prior_warnings": prior_warnings,
        "job_desc": job_desc,
        "cv_rubric": cv_rubric,
        "cv_hints": (cv_hints or "(no hints)"),
        "case_brief": case_brief,
        "project_rubric": project_rubric,
        "report_hints": (report_hints or "(no hints)"),
        "job_desc_short": job_desc_short,
    }

    cv_prompt = _safe_format(CV_PROMPT, base_vars)
    cv_raw = llm.complete_json(cv_prompt)
    cv_res = clamp_cv(cv_raw)

    proj_prompt = (
        _safe_format(PROJECT_PROMPT, base_vars)
        + f"""
[Assistance]
A baseline deterministic score computed from simple keyword buckets is: {baseline_proj}.
- You MUST NOT return a score lower than this deterministic baseline.
- If you adjust upward/downward (≤ ±1.0), justify explicitly in 'project_feedback'.
- Return JSON only.
"""
    )
    proj_raw = llm.complete_json(proj_prompt)
    proj_res = clamp_project(proj_raw)

    try:
        model_score = float(proj_res.project_score)
    except Exception:
        model_score = 1.0
    final_proj_score = max(baseline_proj, model_score)
    if len(report_hints or "") >= 800 and final_proj_score < 2.5:
        final_proj_score = 2.5
        proj_feedback = (
            proj_res.project_feedback or ""
        ) + " [Adjusted: long report content detected; enforced minimum score 2.5 per policy.]"
    else:
        proj_feedback = proj_res.project_feedback

    final_prompt = _safe_format(
        FINAL_PROMPT,
        {
            **base_vars,
            "cv_json": cv_res.json(),
            "project_json": json.dumps(
                {"project_score": final_proj_score, "project_feedback": proj_feedback},
                ensure_ascii=False,
            ),
        },
    )
    final_raw = llm.complete_json(final_prompt)
    final_res = FinalResult(**final_raw)

    return {
        "cv_match_rate": float(cv_res.cv_match_rate),
        "cv_feedback": cv_res.cv_feedback,
        "project_score": float(final_proj_score),
        "project_feedback": proj_feedback,
        "overall_summary": final_res.overall_summary,
        "raw_llm": {
            "cv_raw": cv_raw,
            "proj_raw": proj_raw,
            "final_raw": final_raw,
        },
        "debug": {
            "baseline_proj": baseline_proj,
            "len": {
                "job_desc": len(job_desc or ""),
                "cv_rubric": len(cv_rubric or ""),
                "case_brief": len(case_brief or ""),
                "project_rubric": len(project_rubric or ""),
                "cv_hints": len(cv_hints or ""),
                "report_hints": len(report_hints or ""),
            },
        },
    }
