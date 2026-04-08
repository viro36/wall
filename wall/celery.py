import os
from celery import Celery
from celery.schedules import crontab
import logging

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wall.settings")

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
    from django.core.management import call_command

    try:
        # Выполняем команду без захвата вывода
        call_command(
            "update_organizations_from_dadata",
            "--all",
            "--delay",
            "0.5",
        )
        logger.info("Organizations update completed successfully")
        return "Update completed successfully"

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
