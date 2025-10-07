from django.core.management.base import BaseCommand

from core.models import Document
from core.services.retrieval import retrieval


class Command(BaseCommand):
    help = "Reindex all documents into in-memory vector store (DEV only)."

    def handle(self, *args, **kwargs):
        cnt = 0
        for d in Document.objects.all():
            retrieval.index_document("references", d.storage_path, d.mime_type, str(d.id))
            cnt += 1
        self.stdout.write(self.style.SUCCESS(f"Reindexed {cnt} documents."))
