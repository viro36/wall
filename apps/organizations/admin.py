from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import path
from django.utils.safestring import mark_safe
from .models import District, OrganizationType, Organization
from .dadata_client import get_organization_by_inn


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("short_name", "full_name", "organizations_count")
    search_fields = ("short_name", "full_name")
    ordering = ("short_name",)

    def organizations_count(self, obj):
        return obj.organization_set.count()

    organizations_count.short_description = "Кол-во организаций"


@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "organizations_count")
    search_fields = ("name",)
    ordering = ("name",)

    def organizations_count(self, obj):
        return obj.organization_set.count()

    organizations_count.short_description = "Кол-во организаций"


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "short_name",
        "inn",
        "status_colored",
        "district_link",
        "organization_type_link",
        "show_map_link",
    )

    search_fields = ("short_name", "full_name", "inn", "ogrn")
    list_filter = ("status", "organization_type", "district")
    ordering = ("district", "short_name")

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    ("short_name", "full_name"),
                    ("inn", "kpp", "ogrn"),
                    ("organization_type", "district"),
                    ("status", "coordinates"),
                )
            },
        ),
        (
            "Адрес",
            {
                "fields": (
                    "address_raw",
                    ("postal_code", "region", "city"),
                    ("street", "house"),
                ),
            },
        ),
        (
            "Даты",
            {
                "fields": (("created_at", "updated_at"),),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "show_map_link")
    list_per_page = 50
    actions = ["update_from_dadata"]

    def status_colored(self, obj):
        """Статус с цветом"""
        if not obj.status:
            return "-"

        colors = {
            "ACTIVE": "green",
            "LIQUIDATING": "orange",
            "LIQUIDATED": "red",
        }
        color = colors.get(obj.status, "gray")

        return mark_safe(
            f'<span style="color: {color}; font-weight: bold;">{obj.get_status_display()}</span>'
        )

    status_colored.short_description = "Статус"
    status_colored.admin_order_field = "status"

    def district_link(self, obj):
        """Ссылка на район"""
        if obj.district:
            return mark_safe(
                f'<a href="/admin/organizations/district/{obj.district.id}/change/">{obj.district.short_name}</a>'
            )
        return "-"

    district_link.short_description = "Район"
    district_link.admin_order_field = "district"

    def organization_type_link(self, obj):
        """Ссылка на тип организации"""
        if obj.organization_type:
            return mark_safe(
                f'<a href="/admin/organizations/organizationtype/{obj.organization_type.id}/change/">{obj.organization_type.name}</a>'
            )
        return "-"

    organization_type_link.short_description = "Тип организации"
    organization_type_link.admin_order_field = "organization_type"

    def show_map_link(self, obj):
        """Ссылка на карту (только для детальной страницы)"""
        if obj.coordinates and "," in obj.coordinates:
            parts = obj.coordinates.split(",")
            if len(parts) == 2:
                lat, lon = parts[0].strip(), parts[1].strip()
                return mark_safe(
                    f'<a href="https://yandex.ru/maps/?ll={lon},{lat}&z=17&pt={lon},{lat}" target="_blank">Открыть на карте</a>'
                )
        return "Нет координат"

    show_map_link.short_description = "Карта"

    def update_dadata_button(self, obj):
        """Кнопка обновления данных из DaData"""
        return mark_safe(
            f'<a class="button" href="/admin/organizations/organization/{obj.id}/update-from-dadata/" '
            f'style="background: #28a745; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none;">'
            f"↻ Обновить из DaData</a>"
        )

    update_dadata_button.short_description = "Обновить из DaData"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:pk>/update-from-dadata/",
                self.admin_site.admin_view(self.update_from_dadata_view),
                name="organization-update-from-dadata",
            ),
        ]
        return custom_urls + urls

    def update_from_dadata_view(self, request, pk):
        """Вьюха для обновления организации из DaData"""
        organization = get_object_or_404(Organization, pk=pk)

        # Получаем данные из DaData
        data = get_organization_by_inn(organization.inn)

        if not data:
            messages.error(
                request,
                f"Не удалось получить данные из DaData для ИНН {organization.inn}",
            )
            return redirect("admin:organizations_organization_changelist")

        # Обновляем поля
        updated_fields = []

        if data.get("full_name") and data["full_name"] != organization.full_name:
            organization.full_name = data["full_name"]
            updated_fields.append("полное название")

        if data.get("short_name") and data["short_name"] != organization.short_name:
            organization.short_name = data["short_name"]
            updated_fields.append("краткое название")

        if data.get("kpp") and data["kpp"] != organization.kpp:
            organization.kpp = data["kpp"]
            updated_fields.append("КПП")

        if data.get("ogrn") and data["ogrn"] != organization.ogrn:
            organization.ogrn = data["ogrn"]
            updated_fields.append("ОГРН")

        if data.get("address_raw") and data["address_raw"] != organization.address_raw:
            organization.address_raw = data["address_raw"]
            updated_fields.append("адрес")

        if data.get("postal_code") and data["postal_code"] != organization.postal_code:
            organization.postal_code = data["postal_code"]
            updated_fields.append("индекс")

        if data.get("region") and data["region"] != organization.region:
            organization.region = data["region"]
            updated_fields.append("регион")

        if data.get("city") and data["city"] != organization.city:
            organization.city = data["city"]
            updated_fields.append("город")

        if data.get("street") and data["street"] != organization.street:
            organization.street = data["street"]
            updated_fields.append("улица")

        if data.get("house") and data["house"] != organization.house:
            organization.house = data["house"]
            updated_fields.append("дом")

        if data.get("status") and data["status"] != organization.status:
            status_map = {
                "ACTIVE": "ACTIVE",
                "LIQUIDATING": "LIQUIDATING",
                "LIQUIDATED": "LIQUIDATED",
            }
            organization.status = status_map.get(data["status"], data["status"])
            updated_fields.append("статус")

        if updated_fields:
            organization.save()  # updated_at обновится автоматически
            messages.success(
                request,
                f'Организация обновлена из DaData. Обновлены поля: {", ".join(updated_fields)}',
            )
        else:
            messages.info(request, "Данные актуальны, обновлений не требуется")

        return redirect("admin:organizations_organization_change", pk)

    def update_from_dadata(self, request, queryset):
        """Массовое обновление организаций из DaData"""
        updated_count = 0
        error_count = 0

        for org in queryset:
            data = get_organization_by_inn(org.inn)

            if not data:
                error_count += 1
                continue

            updated = False

            if data.get("full_name") and data["full_name"] != org.full_name:
                org.full_name = data["full_name"]
                updated = True

            if data.get("short_name") and data["short_name"] != org.short_name:
                org.short_name = data["short_name"]
                updated = True

            if data.get("address_raw") and data["address_raw"] != org.address_raw:
                org.address_raw = data["address_raw"]
                updated = True

            if data.get("postal_code") and data["postal_code"] != org.postal_code:
                org.postal_code = data["postal_code"]
                updated = True

            if data.get("region") and data["region"] != org.region:
                org.region = data["region"]
                updated = True

            if data.get("city") and data["city"] != org.city:
                org.city = data["city"]
                updated = True

            if data.get("street") and data["street"] != org.street:
                org.street = data["street"]
                updated = True

            if data.get("house") and data["house"] != org.house:
                org.house = data["house"]
                updated = True

            if data.get("status") and data["status"] != org.status:
                status_map = {
                    "ACTIVE": "ACTIVE",
                    "LIQUIDATING": "LIQUIDATING",
                    "LIQUIDATED": "LIQUIDATED",
                }
                org.status = status_map.get(data["status"], data["status"])
                updated = True

            if updated:
                org.save()  # updated_at обновится автоматически
                updated_count += 1

        if updated_count > 0:
            messages.success(
                request, f"Обновлено {updated_count} организаций из DaData"
            )
        if error_count > 0:
            messages.error(request, f"Не удалось обновить {error_count} организаций")

    update_from_dadata.short_description = "Обновить выбранные из DaData"
