import os
import threading

from django.apps import AppConfig
from django.conf import settings
from django.core.management import call_command


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        if not settings.DEBUG:
            return
        if os.environ.get("AUTO_REINDEX_ON_START", "1") != "1":
            return
        if os.environ.get("RUN_MAIN") != "true":
            return

        def _run():
            try:
                call_command("reindex_all")
            except Exception as e:
                print(f"[auto-reindex] skipped: {e}")

        threading.Thread(target=_run, daemon=True).start()
