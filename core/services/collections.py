import re

_ALLOWED = re.compile(r"[^a-zA-Z0-9._-]")


def ref_collection(refset_id: str, dtype: str) -> str:
    sid = re.sub(r"[^a-zA-Z0-9]", "", refset_id).lower()
    name = f"refset_{sid}_{dtype}".lower()
    name = name.strip("._-")
    if len(name) < 3:
        name = f"rs_{sid or '0'}_{dtype or 'ref'}"
    return name[:120]
