from rest_framework import serializers
from .models import District, OrganizationType, Organization


class DistrictSerializer(serializers.ModelSerializer):
    """Сериализатор для районов"""

    organizations_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = District
        fields = ["id", "short_name", "full_name", "organizations_count"]


class OrganizationTypeSerializer(serializers.ModelSerializer):
    """Сериализатор для типов организаций"""

    organizations_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrganizationType
        fields = ["id", "name", "organizations_count"]


class OrganizationListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка организаций (краткая версия)"""

    district_name = serializers.CharField(source="district.short_name", read_only=True)
    organization_type_name = serializers.CharField(
        source="organization_type.name", read_only=True
    )
    status_display = serializers.SerializerMethodField()
    coordinates_list = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "short_name",
            "full_name",
            "inn",
            "kpp",
            "ogrn",
            "district_name",
            "organization_type_name",
            "status",
            "status_display",
            "coordinates",
            "coordinates_list",
            "address_raw",
        ]

    def get_status_display(self, obj):
        """Получает человекочитаемый статус"""
        return obj.get_status_display()

    def get_coordinates_list(self, obj):
        """Возвращает координаты в виде списка [lat, lon]"""
        if obj.coordinates and "," in obj.coordinates:
            parts = obj.coordinates.split(",")
            if len(parts) == 2:
                return [float(parts[0].strip()), float(parts[1].strip())]
        return None


class OrganizationDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации об организации"""

    district = DistrictSerializer(read_only=True)
    organization_type = OrganizationTypeSerializer(read_only=True)
    status_display = serializers.SerializerMethodField()
    coordinates_list = serializers.SerializerMethodField()
    full_address = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "short_name",
            "full_name",
            "inn",
            "kpp",
            "ogrn",
            "district",
            "organization_type",
            "status",
            "status_display",
            "coordinates",
            "coordinates_list",
            "address_raw",
            "postal_code",
            "region",
            "city",
            "street",
            "house",
            "full_address",
            "created_at",
            "updated_at",
        ]

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_coordinates_list(self, obj):
        if obj.coordinates and "," in obj.coordinates:
            parts = obj.coordinates.split(",")
            if len(parts) == 2:
                return [float(parts[0].strip()), float(parts[1].strip())]
        return None

    def get_full_address(self, obj):
        """Собирает полный адрес из компонентов"""
        parts = []
        if obj.postal_code:
            parts.append(obj.postal_code)
        if obj.region:
            parts.append(obj.region)
        if obj.city:
            parts.append(obj.city)
        if obj.street:
            parts.append(obj.street)
        if obj.house:
            parts.append(obj.house)

        if parts:
            return ", ".join(parts)
        return obj.address_raw


class OrganizationCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления организаций"""

    class Meta:
        model = Organization
        fields = [
            "short_name",
            "full_name",
            "inn",
            "kpp",
            "ogrn",
            "district",
            "organization_type",
            "status",
            "coordinates",
            "address_raw",
            "postal_code",
            "region",
            "city",
            "street",
            "house",
        ]

    def validate_inn(self, value):
        """Валидация ИНН"""
        if value and len(value) not in [10, 12]:
            raise serializers.ValidationError("ИНН должен содержать 10 или 12 цифр")
        return value

    def validate_ogrn(self, value):
        """Валидация ОГРН"""
        if value and len(value) not in [13, 15]:
            raise serializers.ValidationError("ОГРН должен содержать 13 или 15 цифр")
        return value
