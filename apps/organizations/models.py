from django.db import models

class District(models.Model):
    full_name = models.CharField(
        max_length=255,
        verbose_name="Полное название"
    )
    short_name = models.CharField(
        max_length=255,
        verbose_name="Краткое название"
    )

    class Meta:
        verbose_name = "Район"
        verbose_name_plural = "Районы"
        ordering = ['short_name']

    def __str__(self):
        return self.short_name

class OrganizationType(models.Model):
    """Тип организации (профессиональная образовательная организация, школа, вуз и т.д.)"""
    name = models.CharField(
        max_length=255, 
        verbose_name="Название типа"
    )

    class Meta:
        verbose_name = "Тип организации"
        verbose_name_plural = "Типы организаций"

    def __str__(self):
        return self.name


class Organization(models.Model):
    """
    Учебное заведение (или любая организация из DaData).
    Данные будут частично заполняться из API DaData по ИНН.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Действующая'),
        ('LIQUIDATING', 'Ликвидируется'),
        ('LIQUIDATED', 'Ликвидирована'),
        ('REORGANIZING', 'В процессе присоединения к другому юрлицу, с последующей ликвидацией'),
    ]
    
    # Основные реквизиты
    inn = models.CharField(
        max_length=12,
        unique=True,
        db_index=True,
        verbose_name="ИНН"
    )
    kpp = models.CharField(
        max_length=9,
        blank=True,
        null=True,
        verbose_name="КПП"
    )
    ogrn = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="ОГРН"
    )

    # Названия
    full_name = models.TextField(
        verbose_name="Полное наименование"
    )
    short_name = models.CharField(
        max_length=500,
        verbose_name="Краткое наименование"
    )

    # Тип организации
    organization_type = models.ForeignKey(
        OrganizationType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Тип организации"
    )

    # Адрес (полная строка и отдельные поля для аналитики)
    address_raw = models.TextField(
        verbose_name="Адрес (строка)"
    )
    postal_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Индекс"
    )
    region = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Регион"
    )
    city = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Город"
    )
    street = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name="Улица"
    )
    house = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Дом"
    )

    # Координаты
    coordinates = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Координаты (широта, долгота)"
    )

    # Статус организации (из DaData: ACTIVE, LIQUIDATING, LIQUIDATED)
    status = models.CharField(
        max_length=100,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        verbose_name="Статус"
    )

    # Связь с районом (может быть много организаций в одном районе)
    district = models.ForeignKey(
        "District",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Район"
    )

    # Дата создания записи в нашей БД
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"
        indexes = [
            models.Index(fields=['inn']),
            models.Index(fields=['short_name']),
            models.Index(fields=['district']),
            models.Index(fields=['organization_type']),
        ]

    def __str__(self):
        return f"{self.short_name} (ИНН: {self.inn})"
