import time
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from apps.organizations.models import Organization
from apps.organizations.dadata_client import get_organization_by_inn

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Обновляет данные организаций из DaData"

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Обновить все организации",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Максимальное количество организаций для обновления (по умолчанию None - без ограничений)",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.5,
            help="Задержка между запросами в секундах (по умолчанию 0.5)",
        )
        parser.add_argument(
            "--inn",
            type=str,
            help="Обновить организацию по конкретному ИНН",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Обновлять организации, не обновлявшиеся N дней (по умолчанию 7)",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f"=== Начало обновления организаций из DaData ===")
        )
        self.stdout.write(f'Время: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

        # Определяем, какие организации обновлять
        if options["inn"]:
            queryset = Organization.objects.filter(inn=options["inn"])
            self.stdout.write(f'Обновляем организацию с ИНН: {options["inn"]}')
        elif options["all"]:
            queryset = Organization.objects.all()
            if options["limit"]:
                queryset = queryset[: options["limit"]]
                self.stdout.write(
                    f'Обновляем организации (ограничение: {options["limit"]})'
                )
            else:
                self.stdout.write(f"Обновляем ВСЕ организации (без ограничений)")
        else:
            # По умолчанию обновляем только те, которые не обновлялись N дней
            from django.utils import timezone
            from datetime import timedelta

            days_ago = timezone.now() - timedelta(days=options["days"])
            queryset = Organization.objects.filter(updated_at__lt=days_ago).order_by(
                "updated_at"
            )

            if options["limit"]:
                queryset = queryset[: options["limit"]]

            self.stdout.write(
                f'Обновляем организации, не обновлявшиеся {options["days"]} дней'
            )

        total = queryset.count()
        self.stdout.write(f"Найдено организаций для обновления: {total}")

        if total == 0:
            self.stdout.write(self.style.WARNING("Нет организаций для обновления"))
            return

        success_count = 0
        error_count = 0
        skip_count = 0

        for i, org in enumerate(queryset, 1):
            self.stdout.write(
                f"[{i}/{total}] Обновляем {org.short_name} (ИНН: {org.inn})..."
            )

            try:
                # Получаем данные из DaData
                data = get_organization_by_inn(org.inn)

                if not data:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ✗ Не удалось получить данные для ИНН {org.inn}"
                        )
                    )
                    error_count += 1
                    continue

                # Обновляем поля
                with transaction.atomic():
                    updated_fields = []
                    changed = False

                    if data.get("full_name") and data["full_name"] != org.full_name:
                        org.full_name = data["full_name"]
                        updated_fields.append("полное название")
                        changed = True

                    if data.get("short_name") and data["short_name"] != org.short_name:
                        org.short_name = data["short_name"]
                        updated_fields.append("краткое название")
                        changed = True

                    if data.get("kpp") and data["kpp"] != org.kpp:
                        org.kpp = data["kpp"]
                        updated_fields.append("КПП")
                        changed = True

                    if data.get("ogrn") and data["ogrn"] != org.ogrn:
                        org.ogrn = data["ogrn"]
                        updated_fields.append("ОГРН")
                        changed = True

                    if (
                        data.get("address_raw")
                        and data["address_raw"] != org.address_raw
                    ):
                        org.address_raw = data["address_raw"]
                        updated_fields.append("адрес")
                        changed = True

                    if (
                        data.get("postal_code")
                        and data["postal_code"] != org.postal_code
                    ):
                        org.postal_code = data["postal_code"]
                        updated_fields.append("индекс")
                        changed = True

                    if data.get("region") and data["region"] != org.region:
                        org.region = data["region"]
                        updated_fields.append("регион")
                        changed = True

                    if data.get("city") and data["city"] != org.city:
                        org.city = data["city"]
                        updated_fields.append("город")
                        changed = True

                    if data.get("street") and data["street"] != org.street:
                        org.street = data["street"]
                        updated_fields.append("улица")
                        changed = True

                    if data.get("house") and data["house"] != org.house:
                        org.house = data["house"]
                        updated_fields.append("дом")
                        changed = True

                    if data.get("status") and data["status"] != org.status:
                        # Преобразуем статус из DaData в наш формат
                        status_map = {
                            "ACTIVE": "ACTIVE",
                            "LIQUIDATING": "LIQUIDATING",
                            "LIQUIDATED": "LIQUIDATED",
                        }
                        org.status = status_map.get(data["status"], data["status"])
                        updated_fields.append("статус")
                        changed = True

                    if changed:
                        # Сохраняем организацию (updated_at обновится автоматически)
                        org.save()
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Обновлены поля: {", ".join(updated_fields)}'
                            )
                        )
                    else:
                        skip_count += 1
                        self.stdout.write(
                            self.style.WARNING("  – Данные актуальны, обновлений нет")
                        )

                # Задержка между запросами
                if i < total and options["delay"] > 0:
                    time.sleep(options["delay"])

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Ошибка: {str(e)}"))
                error_count += 1
                logger.error(f"Ошибка при обновлении организации {org.inn}: {e}")

        # Выводим итоги
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("=== ИТОГИ ОБНОВЛЕНИЯ ==="))
        self.stdout.write(f"Успешно обновлено: {success_count}")
        self.stdout.write(f"Пропущено (актуальные): {skip_count}")
        self.stdout.write(self.style.ERROR(f"Ошибок: {error_count}"))
        self.stdout.write("=" * 50)
