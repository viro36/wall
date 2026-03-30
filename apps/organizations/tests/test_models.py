import pytest
from apps.organizations.models import District, OrganizationType, Organization


@pytest.mark.django_db
class TestDistrictModel:
    """Тесты для модели District"""

    def test_create_district(self, district):
        """Тест создания района"""
        assert district.full_name == "Центральный административный округ"
        assert district.short_name == "ЦАО"
        assert str(district) == "ЦАО"

    def test_district_ordering(self, db):
        """Тест сортировки районов"""
        District.objects.create(full_name="Южный округ", short_name="ЮАО")
        District.objects.create(full_name="Северный округ", short_name="САО")
        District.objects.create(full_name="Центральный округ", short_name="ЦАО")

        districts = District.objects.all()
        assert districts[0].short_name == "САО"
        assert districts[1].short_name == "ЦАО"
        assert districts[2].short_name == "ЮАО"

    def test_district_str_method(self, district):
        """Тест строкового представления"""
        assert str(district) == district.short_name


@pytest.mark.django_db
class TestOrganizationTypeModel:
    """Тесты для модели OrganizationType"""

    def test_create_organization_type(self, organization_type):
        """Тест создания типа организации"""
        assert organization_type.name == "Школа"
        assert str(organization_type) == "Школа"

    def test_organization_type_ordering(self, db):
        """Тест сортировки типов организаций (по алфавиту)"""
        OrganizationType.objects.create(name="Детский сад")
        OrganizationType.objects.create(name="Школа")
        OrganizationType.objects.create(name="ВУЗ")

        types = OrganizationType.objects.all().order_by("name")
        assert types[0].name == "ВУЗ"
        assert types[1].name == "Детский сад"
        assert types[2].name == "Школа"

    def test_organization_type_str_method(self, organization_type):
        """Тест строкового представления"""
        assert str(organization_type) == organization_type.name


@pytest.mark.django_db
class TestOrganizationModel:
    """Тесты для модели Organization"""

    def test_create_organization(self, organization):
        """Тест создания организации"""
        assert organization.inn == "7701234567"
        assert organization.short_name == "ГБОУ Школа №1"
        assert (
            str(organization) == f"{organization.short_name} (ИНН: {organization.inn})"
        )
        assert organization.status == "ACTIVE"

    def test_organization_relations(self, organization, district, organization_type):
        """Тест связей организации"""
        assert organization.district == district
        assert organization.organization_type == organization_type
        assert organization.district.short_name == "ЦАО"
        assert organization.organization_type.name == "Школа"

    def test_organization_unique_inn(self, organization):
        """Тест уникальности ИНН"""
        with pytest.raises(Exception):
            Organization.objects.create(
                inn="7701234567",  # Тот же ИНН
                short_name="Другая школа",
                full_name="Другая школа",
            )

    def test_organization_status_choices(self, organization, inactive_organization):
        """Тест выбора статуса"""
        assert organization.status == "ACTIVE"
        assert inactive_organization.status == "LIQUIDATED"

        assert organization.get_status_display() == "Действующая"
        assert inactive_organization.get_status_display() == "Ликвидирована"

    def test_organization_nullable_fields(self, db):
        """Тест опциональных полей"""
        org = Organization.objects.create(
            inn="7701234570", short_name="Тест", full_name="Тестовая организация"
        )
        assert org.kpp is None
        assert org.ogrn is None
        assert org.organization_type is None
        assert org.district is None
        assert org.coordinates is None
        assert org.postal_code is None

    def test_organization_coordinates_parsing(self, organization):
        """Тест парсинга координат"""
        assert organization.coordinates == "55.7558, 37.6173"

        if organization.coordinates and "," in organization.coordinates:
            parts = organization.coordinates.split(",")
            if len(parts) == 2:
                lat, lon = float(parts[0].strip()), float(parts[1].strip())
                assert lat == 55.7558
                assert lon == 37.6173

    def test_organization_str_method_without_inn(self, db):
        """Тест строкового представления организации без ИНН"""
        org = Organization.objects.create(
            short_name="Тестовая организация", full_name="Тестовая организация"
        )
        # Проверяем, что строковое представление содержит short_name
        assert org.short_name in str(org)
        # Проверяем, что представление не содержит None или пустые значения
        assert "None" not in str(org)

    def test_organization_cascade_delete_district(self, organization, district):
        """Тест: при удалении района организация не удаляется"""
        district.delete()
        organization.refresh_from_db()
        assert organization.district is None

    def test_organization_cascade_delete_type(self, organization, organization_type):
        """Тест: при удалении типа организации организация не удаляется"""
        organization_type.delete()
        organization.refresh_from_db()
        assert organization.organization_type is None
