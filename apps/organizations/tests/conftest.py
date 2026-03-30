import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from apps.organizations.models import District, OrganizationType, Organization


@pytest.fixture
def api_client():
    """Фикстура для API клиента"""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Фикстура для администратора"""
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="admin123"
    )


@pytest.fixture
def regular_user(db):
    """Фикстура для обычного пользователя"""
    return User.objects.create_user(
        username="user", email="user@example.com", password="user123"
    )


@pytest.fixture
def district(db):
    """Фикстура для района"""
    return District.objects.create(
        full_name="Центральный административный округ", short_name="ЦАО"
    )


@pytest.fixture
def another_district(db):
    """Фикстура для другого района"""
    return District.objects.create(
        full_name="Южный административный округ", short_name="ЮАО"
    )


@pytest.fixture
def organization_type(db):
    """Фикстура для типа организации"""
    return OrganizationType.objects.create(name="Школа")


@pytest.fixture
def another_organization_type(db):
    """Фикстура для другого типа организации"""
    return OrganizationType.objects.create(name="Детский сад")


@pytest.fixture
def organization(db, district, organization_type):
    """Фикстура для организации"""
    return Organization.objects.create(
        inn="7701234567",
        kpp="770101001",
        ogrn="1027700123456",
        full_name="Государственное бюджетное общеобразовательное учреждение Школа №1",
        short_name="ГБОУ Школа №1",
        organization_type=organization_type,
        district=district,
        address_raw="г. Москва, ул. Ленина, д. 1",
        postal_code="101000",
        region="г. Москва",
        city="Москва",
        street="ул. Ленина",
        house="1",
        coordinates="55.7558, 37.6173",
        status="ACTIVE",
    )


@pytest.fixture
def another_organization(db, another_district, another_organization_type):
    """Фикстура для другой организации"""
    return Organization.objects.create(
        inn="7701234568",
        kpp="770101002",
        ogrn="1027700123457",
        full_name="Государственное бюджетное дошкольное образовательное учреждение Детский сад №2",
        short_name="ГБДОУ Детский сад №2",
        organization_type=another_organization_type,
        district=another_district,
        address_raw="г. Москва, ул. Пушкина, д. 2",
        postal_code="101001",
        region="г. Москва",
        city="Москва",
        street="ул. Пушкина",
        house="2",
        coordinates="55.7559, 37.6174",
        status="ACTIVE",
    )


@pytest.fixture
def inactive_organization(db, district, organization_type):
    """Фикстура для неактивной организации"""
    return Organization.objects.create(
        inn="7701234569",
        kpp="770101003",
        ogrn="1027700123458",
        full_name="Ликвидированная организация",
        short_name="ООО Ромашка",
        organization_type=organization_type,
        district=district,
        address_raw="г. Москва, ул. Гоголя, д. 3",
        status="LIQUIDATED",
    )
