from typing import Dict, List  # noqa: UP035


def simple_chunk(text: str, max_chars: int = 800) -> List[Dict]:  # noqa: UP006
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i : i + max_chars]
        chunks.append({"text": chunk, "meta": {"offset": i}})
        i += max_chars
    return chunks
