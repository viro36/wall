import pytest
from django.db.models import Count
from apps.organizations.models import District, OrganizationType
from apps.organizations.serializers import (
    DistrictSerializer,
    OrganizationTypeSerializer,
    OrganizationListSerializer,
    OrganizationDetailSerializer,
    OrganizationCreateUpdateSerializer,
)


@pytest.mark.django_db
class TestDistrictSerializer:
    """Тесты сериализатора для районов"""

    def test_district_serializer(self, district):
        """Тест базовой сериализации района"""
        # Используем тот же queryset, что и в view
        district_with_count = (
            District.objects.filter(id=district.id)
            .annotate(organizations_count=Count("organization"))
            .first()
        )

        serializer = DistrictSerializer(district_with_count)
        data = serializer.data

        assert data["id"] == district.id
        assert data["short_name"] == "ЦАО"
        assert data["full_name"] == "Центральный административный округ"
        assert "organizations_count" in data
        assert data["organizations_count"] == 0  # У этого района пока нет организаций


@pytest.mark.django_db
class TestOrganizationTypeSerializer:
    """Тесты сериализатора для типов организаций"""

    def test_organization_type_serializer(self, organization_type):
        """Тест базовой сериализации типа организации"""
        # Используем тот же queryset, что и в view
        org_type_with_count = (
            OrganizationType.objects.filter(id=organization_type.id)
            .annotate(organizations_count=Count("organization"))
            .first()
        )

        serializer = OrganizationTypeSerializer(org_type_with_count)
        data = serializer.data

        assert data["id"] == organization_type.id
        assert data["name"] == "Школа"
        assert "organizations_count" in data
        assert data["organizations_count"] == 0  # У этого типа пока нет организаций


@pytest.mark.django_db
class TestOrganizationListSerializer:
    """Тесты сериализатора списка организаций"""

    def test_organization_list_serializer(self, organization):
        """Тест сериализации списка организаций"""
        serializer = OrganizationListSerializer(organization)
        data = serializer.data

        assert data["id"] == organization.id
        assert data["short_name"] == "ГБОУ Школа №1"
        assert (
            data["full_name"]
            == "Государственное бюджетное общеобразовательное учреждение Школа №1"
        )
        assert data["inn"] == "7701234567"
        assert data["kpp"] == "770101001"
        assert data["ogrn"] == "1027700123456"
        assert data["district_name"] == "ЦАО"
        assert data["organization_type_name"] == "Школа"
        assert data["status"] == "ACTIVE"
        assert data["status_display"] == "Действующая"
        assert data["coordinates"] == "55.7558, 37.6173"
        assert data["coordinates_list"] == [55.7558, 37.6173]
        assert data["address_raw"] == "г. Москва, ул. Ленина, д. 1"

    def test_organization_list_serializer_no_coordinates(self, inactive_organization):
        """Тест сериализации организации без координат"""
        serializer = OrganizationListSerializer(inactive_organization)
        data = serializer.data

        assert data["coordinates"] is None
        assert data["coordinates_list"] is None


@pytest.mark.django_db
class TestOrganizationDetailSerializer:
    """Тесты сериализатора детальной информации организации"""

    def test_organization_detail_serializer(self, organization):
        """Тест детальной сериализации организации"""
        serializer = OrganizationDetailSerializer(organization)
        data = serializer.data

        assert data["id"] == organization.id
        assert data["short_name"] == "ГБОУ Школа №1"
        assert (
            data["full_name"]
            == "Государственное бюджетное общеобразовательное учреждение Школа №1"
        )
        assert data["inn"] == "7701234567"
        assert data["kpp"] == "770101001"
        assert data["ogrn"] == "1027700123456"
        assert data["district"]["id"] == organization.district.id
        assert data["district"]["short_name"] == "ЦАО"
        assert data["district"]["full_name"] == "Центральный административный округ"
        assert data["organization_type"]["id"] == organization.organization_type.id
        assert data["organization_type"]["name"] == "Школа"
        assert data["status"] == "ACTIVE"
        assert data["status_display"] == "Действующая"
        assert data["coordinates"] == "55.7558, 37.6173"
        assert data["coordinates_list"] == [55.7558, 37.6173]
        assert data["address_raw"] == "г. Москва, ул. Ленина, д. 1"
        assert data["postal_code"] == "101000"
        assert data["region"] == "г. Москва"
        assert data["city"] == "Москва"
        assert data["street"] == "ул. Ленина"
        assert data["house"] == "1"
        # Проверяем full_address
        assert "101000" in data["full_address"]
        assert "г. Москва" in data["full_address"]
        assert "ул. Ленина" in data["full_address"]
        assert "1" in data["full_address"]

    def test_organization_detail_full_address(self, organization):
        """Тест формирования полного адреса"""
        serializer = OrganizationDetailSerializer(organization)
        data = serializer.data
        # Проверяем, что full_address содержит все компоненты
        assert data["full_address"] == "101000, г. Москва, Москва, ул. Ленина, 1"


@pytest.mark.django_db
class TestOrganizationCreateUpdateSerializer:
    """Тесты сериализатора создания/обновления организаций"""

    def test_organization_create_serializer_valid(self, district, organization_type):
        """Тест валидных данных для создания"""
        data = {
            "short_name": "Новая школа",
            "full_name": "Новая школа №3",
            "inn": "7701234571",
            "kpp": "770101004",
            "ogrn": "1027700123459",
            "district": district.id,
            "organization_type": organization_type.id,
            "address_raw": "г. Москва, ул. Новая, д. 1",
            "status": "ACTIVE",
        }
        serializer = OrganizationCreateUpdateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["short_name"] == "Новая школа"
        assert serializer.validated_data["inn"] == "7701234571"

    def test_organization_create_serializer_invalid_inn(
        self, district, organization_type
    ):
        """Тест невалидного ИНН"""
        data = {
            "short_name": "Новая школа",
            "full_name": "Новая школа №3",
            "inn": "123",  # Слишком короткий
            "district": district.id,
            "organization_type": organization_type.id,
            "address_raw": "г. Москва, ул. Новая, д. 1",
        }
        serializer = OrganizationCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert "inn" in serializer.errors

    def test_organization_create_serializer_invalid_ogrn(
        self, district, organization_type
    ):
        """Тест невалидного ОГРН"""
        data = {
            "short_name": "Новая школа",
            "full_name": "Новая школа №3",
            "inn": "7701234571",
            "ogrn": "123",  # Слишком короткий
            "district": district.id,
            "organization_type": organization_type.id,
            "address_raw": "г. Москва, ул. Новая, д. 1",
        }
        serializer = OrganizationCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert "ogrn" in serializer.errors

    def test_organization_create_serializer_minimal_fields(self, db):
        """Тест минимальных обязательных полей"""
        data = {
            "short_name": "Минимальная организация",
            "full_name": "Минимальная организация",
            "inn": "7701234572",
            "address_raw": "г. Москва, ул. Минимальная, д. 1",
        }
        serializer = OrganizationCreateUpdateSerializer(data=data)
        assert serializer.is_valid()

        # Сохраняем организацию
        organization = serializer.save()
        assert organization.short_name == "Минимальная организация"
        assert organization.district is None
        assert organization.organization_type is None
        assert organization.status is None
