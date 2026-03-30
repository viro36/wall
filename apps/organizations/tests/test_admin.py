import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from apps.organizations.admin import (
    DistrictAdmin,
    OrganizationTypeAdmin,
    OrganizationAdmin,
)
from apps.organizations.models import District, OrganizationType, Organization


class TestDistrictAdmin:
    """Тесты для админки районов"""

    @pytest.mark.django_db
    def test_district_admin_list_display(self, admin_user):
        """Тест отображения полей в списке"""
        site = AdminSite()
        admin = DistrictAdmin(District, site)

        # Проверяем, что поля для отображения настроены
        assert "short_name" in admin.list_display
        assert "full_name" in admin.list_display
        assert "organizations_count" in admin.list_display

    @pytest.mark.django_db
    def test_district_admin_search_fields(self):
        """Тест полей поиска"""
        site = AdminSite()
        admin = DistrictAdmin(District, site)

        assert "short_name" in admin.search_fields
        assert "full_name" in admin.search_fields


class TestOrganizationTypeAdmin:
    """Тесты для админки типов организаций"""

    @pytest.mark.django_db
    def test_organization_type_admin_list_display(self):
        """Тест отображения полей в списке"""
        site = AdminSite()
        admin = OrganizationTypeAdmin(OrganizationType, site)

        assert "name" in admin.list_display
        assert "organizations_count" in admin.list_display

    @pytest.mark.django_db
    def test_organization_type_admin_search_fields(self):
        """Тест полей поиска"""
        site = AdminSite()
        admin = OrganizationTypeAdmin(OrganizationType, site)

        assert "name" in admin.search_fields


class TestOrganizationAdmin:
    """Тесты для админки организаций"""

    @pytest.mark.django_db
    def test_organization_admin_list_display(self):
        """Тест отображения полей в списке"""
        site = AdminSite()
        admin = OrganizationAdmin(Organization, site)

        assert "short_name" in admin.list_display
        assert "inn" in admin.list_display
        assert "status_colored" in admin.list_display

    @pytest.mark.django_db
    def test_organization_admin_search_fields(self):
        """Тест полей поиска"""
        site = AdminSite()
        admin = OrganizationAdmin(Organization, site)

        assert "short_name" in admin.search_fields
        assert "full_name" in admin.search_fields
        assert "inn" in admin.search_fields

    @pytest.mark.django_db
    def test_organization_admin_list_filter(self):
        """Тест фильтров"""
        site = AdminSite()
        admin = OrganizationAdmin(Organization, site)

        assert "status" in admin.list_filter
        assert "organization_type" in admin.list_filter
        assert "district" in admin.list_filter
