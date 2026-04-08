import os
import sys
from celery import Celery
from celery.schedules import crontab
import logging

# Устанавливаем UTF-8
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wall.settings")
os.environ["PYTHONIOENCODING"] = "utf-8"

logger = logging.getLogger(__name__)

app = Celery("wall")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


# Задача для обновления организаций
@app.task
def update_organizations_from_dadata():
    """Задача для периодического обновления организаций из DaData"""
    import subprocess

    try:
        # Запускаем команду через subprocess с правильной кодировкой
        result = subprocess.run(
            [
                "python",
                "manage.py",
                "update_organizations_from_dadata",
                "--all",
                "--delay",
                "0.5",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd="/App",
        )

        if result.returncode == 0:
            logger.info("Organizations update completed successfully")
            return "Update completed successfully"
        else:
            logger.error(f"Error: {result.stderr[:500]}")
            return f"Error: {result.stderr[:500]}"

    except Exception as e:
        logger.error(f"Error updating organizations: {str(e)}")
        return f"Error: {str(e)}"


# Настройка периодических задач
app.conf.beat_schedule = {
    "update-organizations-every-friday": {
        "task": "wall.celery.update_organizations_from_dadata",
        "schedule": crontab(day_of_week="friday", hour=2, minute=0),
        "args": (),
    },
}
