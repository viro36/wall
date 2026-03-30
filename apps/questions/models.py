from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field

from apps.organizations.models import Organization


class Comment(models.Model):
    """
    Универсальная модель комментариев
    Может прикрепляться к Question, Suggestion или другому объекту
    """

    # Информация об авторе
    author_name = models.CharField(max_length=255, verbose_name="ФИО или Ник")

    # Содержание комментария
    content = models.TextField(verbose_name="Текст комментария")

    # Generic Foreign Key - комментарий может быть привязан к любой модели
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, verbose_name="Тип объекта"
    )
    object_id = models.PositiveIntegerField(verbose_name="ID объекта")
    content_object = GenericForeignKey("content_type", "object_id")

    # Для ответов на комментарии (древовидная структура)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name="Родительский комментарий",
    )

    # Статистика
    # likes_count = models.PositiveIntegerField(default=0, verbose_name="Лайки")

    # Модерация
    is_approved = models.BooleanField(default=True, verbose_name="Одобрено")
    is_deleted = models.BooleanField(default=False, verbose_name="Удален")

    # Кто и когда удалил
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_comments",
        verbose_name="Кто удалил",
    )
    deleted_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата удаления"
    )

    # Мета-информация
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["is_approved"]),
            models.Index(fields=["is_deleted"]),
        ]

    def __str__(self):
        if self.is_deleted:
            return f"Удаленный комментарий (был от {self.author_name})"
        return f"Комментарий от {self.author_name} к {self.content_object}"

    @property
    def is_reply(self):
        """Является ли комментарий ответом на другой комментарий"""
        return self.parent is not None

    def get_absolute_url(self):
        """Ссылка на объект комментария"""
        if self.content_object:
            if hasattr(self.content_object, "get_absolute_url"):
                return self.content_object.get_absolute_url()
        return "#"


class Question(models.Model):
    """
    Модель вопроса от пользователя
    """

    STATUS_CHOICES = [
        ("new", "Новый"),  # Только создан
        ("processing", "В обработке"),  # Админ взял в работу
        ("has_suggestions", "Есть предложения"),  # Появились предложения
        ("has_best", "Есть лучшее"),  # Админ отметил лучшее
        ("closed", "Закрыт"),  # Вопрос закрыт
    ]

    # Связь с организацией
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="questions",
    )

    # Информация об авторе
    author_name = models.CharField(max_length=255, verbose_name="ФИО или Ник")
    author_email = models.EmailField(
        blank=True, null=True, verbose_name="Email для уведомлений"
    )

    # Содержание вопроса
    title = models.CharField(max_length=500, verbose_name="Заголовок вопроса")
    content = CKEditor5Field(
        verbose_name="Текст вопроса",
        config_name="extends",  # Используем расширенную конфигурацию
    )

    # Статусы
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="new", verbose_name="Статус"
    )
    status_changed_at = models.DateTimeField(
        auto_now=True, verbose_name="Дата изменения статуса"
    )

    # Кто взял в обработку (для status='processing')
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_questions",
        verbose_name="Кто взял в обработку",
    )
    processed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата взятия в обработку"
    )

    # Статистика
    views_count = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    suggestions_count = models.PositiveIntegerField(
        default=0, verbose_name="Количество предложений"
    )

    # Модерация
    is_approved = models.BooleanField(default=True, verbose_name="Одобрено")

    comments = GenericRelation(
        Comment,
        content_type_field="content_type",
        object_id_field="object_id",
        related_name="question_comments",  # уникальное имя
        verbose_name="Комментарии",
    )

    # Мета-информация
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["organization"]),
        ]

    def __str__(self):
        return f"{self.title[:50]}... ({self.author_name})"

    def save(self, *args, **kwargs):
        """Автоматически обновляем дату взятия в обработку"""
        if self.status == "processing" and not self.processed_at:
            self.processed_at = timezone.now()
        super().save(*args, **kwargs)


class Suggestion(models.Model):
    """
    Предложение/ответ на вопрос
    """

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="suggestions",
        verbose_name="Вопрос",
    )

    # Информация об авторе
    author_name = models.CharField(max_length=255, verbose_name="ФИО или Ник")
    author_email = models.EmailField(
        blank=True, null=True, verbose_name="Email для уведомлений"
    )

    # Связь с организацией
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="suggestions",
    )

    # Содержание
    content = models.TextField(verbose_name="Текст предложения")

    # Реакции (лайки/дизлайки + эмоджи)
    likes_count = models.PositiveIntegerField(default=0, verbose_name="Лайки")
    dislikes_count = models.PositiveIntegerField(default=0, verbose_name="Дизлайки")

    # Эмоджи-реакции
    reactions = models.JSONField(
        default=dict, blank=True, verbose_name="Реакции (эмоджи)"
    )

    # Отметка "лучшее предложение"
    is_best = models.BooleanField(default=False, verbose_name="Лучшее предложение")
    marked_as_best_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата отметки лучшим"
    )
    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marked_suggestions",
        verbose_name="Кто отметил лучшим",
    )

    # Модерация
    is_approved = models.BooleanField(default=True, verbose_name="Одобрено")

    comments = GenericRelation(
        Comment,
        content_type_field="content_type",
        object_id_field="object_id",
        related_name="suggestion_comments",  # уникальное имя
        verbose_name="Комментарии",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Предложение"
        verbose_name_plural = "Предложения"
        ordering = ["-is_best", "-likes_count", "created_at"]

    def __str__(self):
        return f"Предложение к {self.question.id} от {self.author_name}"

    def update_votes_count(self):
        """Обновляет счетчики лайков/дизлайков на основе голосов"""
        self.likes_count = self.votes.filter(vote=1).count()
        self.dislikes_count = self.votes.filter(vote=-1).count()
        self.save(update_fields=["likes_count", "dislikes_count"])


class Vote(models.Model):
    """
    Отдельная модель для голосований (лайки/дизлайки)
    Анонимное голосование через сессию
    """

    VOTE_CHOICES = [
        (1, "Лайк"),
        (-1, "Дизлайк"),
    ]

    suggestion = models.ForeignKey(
        Suggestion,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name="Предложение",
    )

    # Идентификация по сессии
    voter_session = models.CharField(max_length=255, verbose_name="Сессия голосующего")

    vote = models.SmallIntegerField(choices=VOTE_CHOICES, verbose_name="Голос")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата голоса")

    class Meta:
        verbose_name = "Голос"
        verbose_name_plural = "Голоса"
        unique_together = ["suggestion", "voter_session"]  # Один голос с одной сессии
        indexes = [
            models.Index(fields=["suggestion", "voter_session"]),
        ]

    def __str__(self):
        vote_display = "+" if self.vote == 1 else "-"
        return f"{vote_display} от сессии {self.voter_session[:8]}..."
