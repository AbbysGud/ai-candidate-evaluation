# core/services/rag.py
from .retrieval import retrieval
from .collections import ref_collection


def fetch_cv_context(job_title: str, reference_set_id: str, top_k=6):
    col_jd = ref_collection(reference_set_id, "job_desc")
    col_rub = ref_collection(reference_set_id, "scoring_rubric")

    jd_hits = retrieval.search(col_jd, f"{job_title} backend cloud api", top_k=top_k)
    rub_hits = retrieval.search(col_rub, "cv rubric backend", top_k=top_k)

    print(
        "[RAG HITS CV]",
        {"col_jd": col_jd, "jd": len(jd_hits), "col_rub": col_rub, "rub": len(rub_hits)},
    )

    job_desc = "\n---\n".join([h["text"] for h in jd_hits])
    cv_rubric = "\n---\n".join([h["text"] for h in rub_hits])
    return job_desc, cv_rubric


def fetch_project_context(reference_set_id: str, top_k=6):
    col_cb = ref_collection(reference_set_id, "case_brief")
    col_rub = ref_collection(reference_set_id, "scoring_rubric")

    cb_hits = retrieval.search(col_cb, "backend case brief rag", top_k=top_k)
    rub_hits = retrieval.search(col_rub, "project rubric backend", top_k=top_k)

    print(
        "[RAG HITS PROJ]",
        {"col_cb": col_cb, "cb": len(cb_hits), "col_rub": col_rub, "rub": len(rub_hits)},
    )

    case_brief = "\n---\n".join([h["text"] for h in cb_hits])
    project_rubric = "\n---\n".join([h["text"] for h in rub_hits])
    return case_brief, project_rubric
