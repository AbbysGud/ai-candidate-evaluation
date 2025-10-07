from pathlib import Path

from django.conf import settings


class LocalStorage:
    root = Path(settings.MEDIA_ROOT)

    def save(self, rel_path: str, content) -> str:
        p = self.root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            if hasattr(content, "chunks"):
                for c in content.chunks():
                    f.write(c)
            else:
                f.write(content)
        return str(p)

    def read_text(self, rel_path: str, encoding="utf-8") -> str:
        return (self.root / rel_path).read_text(encoding=encoding)

    def exists(self, rel_path: str) -> bool:
        return (self.root / rel_path).exists()
