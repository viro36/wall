from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html, mark_safe
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import Question, Suggestion, Comment, Vote


class CommentInline(GenericTabularInline):
    """
    Инлайн для комментариев (для вопросов и предложений)
    """

    model = Comment
    fields = ["author_name", "content", "created_at", "is_approved"]
    readonly_fields = ["created_at"]
    extra = 0
    ct_field = "content_type"
    ct_fk_field = "object_id"


class VoteInline(admin.TabularInline):
    """
    Инлайн для голосов (для предложений)
    """

    model = Vote
    fields = ["vote_display", "voter_session", "created_at"]
    readonly_fields = ["vote_display", "voter_session", "created_at"]
    extra = 0
    can_delete = False

    def vote_display(self, obj):
        return "+" if obj.vote == 1 else "-"

    vote_display.short_description = "Голос"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Админка для вопросов
    """

    list_display = [
        "id",
        "title_short",
        "author_name",
        "organization_info",
        "status_colored",
        "suggestions_count",
        "views_count",
        "created_at_short",
    ]

    list_filter = [
        "status",
        "is_approved",
        "organization__district",
        "organization__organization_type",
        "created_at",
    ]

    search_fields = ["title", "content", "author_name", "author_email"]

    readonly_fields = [
        "created_at",
        "updated_at",
        "status_changed_at",
        "processed_at",
        "suggestions_count",
        "views_count",
        "comments_link",
    ]

    fieldsets = [
        ("Автор", {"fields": ["author_name", "author_email"]}),
        ("Организация", {"fields": ["organization"]}),
        ("Вопрос", {"fields": ["title", "content"]}),
        (
            "Статус и обработка",
            {"fields": ["status", "status_changed_at", "processed_by", "processed_at"]},
        ),
        (
            "Статистика",
            {"fields": ["views_count", "suggestions_count", "comments_link"]},
        ),
        ("Модерация", {"fields": ["is_approved"]}),
        ("Даты", {"fields": ["created_at", "updated_at"], "classes": ["collapse"]}),
    ]

    inlines = [CommentInline]

    list_per_page = 50
    date_hierarchy = "created_at"

    actions = [
        "mark_as_processing",
        "mark_as_has_best",
        "mark_as_closed",
        "approve_questions",
    ]

    def title_short(self, obj):
        """Короткий заголовок"""
        return obj.title[:50] + "..." if len(obj.title) > 50 else obj.title

    title_short.short_description = "Заголовок"
    title_short.admin_order_field = "title"

    def organization_info(self, obj):
        """Информация об организации"""
        if obj.organization:
            return format_html(
                "{}<br><small>{} / {}</small>",
                obj.organization.short_name,
                (
                    obj.organization.district.short_name
                    if obj.organization.district
                    else "-"
                ),
                (
                    obj.organization.organization_type.name
                    if obj.organization.organization_type
                    else "-"
                ),
            )
        return "-"

    organization_info.short_description = "Организация"

    def status_colored(self, obj):
        """Статус с цветом"""
        colors = {
            "new": "gray",
            "processing": "orange",
            "has_suggestions": "blue",
            "has_best": "green",
            "closed": "red",
        }
        color = colors.get(obj.status, "gray")

        status_display = dict(Question.STATUS_CHOICES).get(obj.status, obj.status)

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status_display,
        )

    status_colored.short_description = "Статус"
    status_colored.admin_order_field = "status"

    def created_at_short(self, obj):
        """Короткая дата создания"""
        return obj.created_at.strftime("%d.%m.%Y %H:%M")

    created_at_short.short_description = "Создан"
    created_at_short.admin_order_field = "created_at"

    def comments_link(self, obj):
        """Ссылка на комментарии"""
        count = obj.comments.count()
        return format_html(
            '<a href="/admin/questions/comment/?question_comments__id={}">{} комментариев</a>',
            obj.id,
            count,
        )

    comments_link.short_description = "Комментарии"

    def mark_as_processing(self, request, queryset):
        """Отметить как в обработке"""
        updated = queryset.update(
            status="processing",
            processed_at=timezone.now(),
            processed_by=request.user if request.user.is_authenticated else None,
        )
        self.message_user(request, f'{updated} вопросов отмечены как "В обработке"')

    mark_as_processing.short_description = "Отметить как В ОБРАБОТКЕ"

    def mark_as_has_best(self, request, queryset):
        """Отметить как есть лучшее предложение"""
        updated = queryset.update(status="has_best")
        self.message_user(request, f'{updated} вопросов отмечены как "Есть лучшее"')

    mark_as_has_best.short_description = "Отметить как ЕСТЬ ЛУЧШЕЕ"

    def mark_as_closed(self, request, queryset):
        """Закрыть вопросы"""
        updated = queryset.update(status="closed")
        self.message_user(request, f"{updated} вопросов закрыты")

    mark_as_closed.short_description = "Закрыть вопросы"

    def approve_questions(self, request, queryset):
        """Одобрить вопросы"""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} вопросов одобрены")

    approve_questions.short_description = "Одобрить выбранные"


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    """
    Админка для предложений
    """

    list_display = [
        "id",
        "question_link",
        "author_name",
        "content_short",
        "votes_display",
        "is_best_colored",
        "created_at_short",
    ]

    list_filter = ["is_best", "is_approved", "created_at"]

    search_fields = ["content", "author_name", "author_email"]

    readonly_fields = [
        "created_at",
        "updated_at",
        "marked_as_best_at",
        "likes_count",
        "dislikes_count",
        "reactions",
        "votes_preview",
        "comments_link",
    ]

    fieldsets = [
        ("Вопрос", {"fields": ["question"]}),
        ("Автор", {"fields": ["author_name", "author_email"]}),
        ("Предложение", {"fields": ["content"]}),
        (
            "Лучшее предложение",
            {"fields": ["is_best", "marked_as_best_at", "marked_by"]},
        ),
        (
            "Статистика",
            {
                "fields": [
                    "votes_preview",
                    "likes_count",
                    "dislikes_count",
                    "reactions",
                    "comments_link",
                ]
            },
        ),
        ("Модерация", {"fields": ["is_approved"]}),
        ("Даты", {"fields": ["created_at", "updated_at"], "classes": ["collapse"]}),
    ]

    inlines = [CommentInline, VoteInline]

    list_per_page = 50
    date_hierarchy = "created_at"

    actions = ["mark_as_best", "unmark_as_best", "approve_suggestions"]

    def question_link(self, obj):
        """Ссылка на вопрос"""
        return format_html(
            '<a href="/admin/questions/question/{}/change/">Вопрос #{}</a>',
            obj.question.id,
            obj.question.id,
        )

    question_link.short_description = "Вопрос"

    def content_short(self, obj):
        """Короткое содержание"""
        return obj.content[:75] + "..." if len(obj.content) > 75 else obj.content

    content_short.short_description = "Предложение"

    def votes_display(self, obj):
        """Отображение голосов"""
        return format_html("+ {} | - {}", obj.likes_count, obj.dislikes_count)

    votes_display.short_description = "Голоса"

    def is_best_colored(self, obj):
        """Отметка лучшего с цветом"""
        if obj.is_best:
            return mark_safe(
                '<span style="color: gold; font-weight: bold;">Лучшее</span>'
            )
        return mark_safe("—")

    is_best_colored.short_description = "Лучшее"

    def created_at_short(self, obj):
        return obj.created_at.strftime("%d.%m.%Y %H:%M")

    created_at_short.short_description = "Создано"

    def votes_preview(self, obj):
        """Предпросмотр голосов"""
        votes = obj.votes.all()[:10]
        if not votes:
            return mark_safe("—")

        result = ""
        for vote in votes:
            result += "+ " if vote.vote == 1 else "- "
        if obj.votes.count() > 10:
            result += f" и ещё {obj.votes.count() - 10}"
        return result

    votes_preview.short_description = "Последние голоса"

    def comments_link(self, obj):
        count = obj.comments.count()
        return format_html(
            '<a href="/admin/questions/comment/?suggestion_comments__id={}">{} комментариев</a>',
            obj.id,
            count,
        )

    comments_link.short_description = "Комментарии"

    def mark_as_best(self, request, queryset):
        """Отметить как лучшее"""
        updated = queryset.update(
            is_best=True,
            marked_as_best_at=timezone.now(),
            marked_by=request.user if request.user.is_authenticated else None,
        )
        # Обновляем статус связанных вопросов
        for suggestion in queryset:
            suggestion.question.status = "has_best"
            suggestion.question.save()

        self.message_user(request, f"{updated} предложений отмечены как лучшие")

    mark_as_best.short_description = "Отметить как ЛУЧШЕЕ"

    def unmark_as_best(self, request, queryset):
        """Снять отметку лучшего"""
        updated = queryset.update(is_best=False, marked_as_best_at=None, marked_by=None)
        self.message_user(request, f'Снята отметка "лучшее" с {updated} предложений')

    unmark_as_best.short_description = "Снять отметку ЛУЧШЕЕ"

    def approve_suggestions(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} предложений одобрены")

    approve_suggestions.short_description = "Одобрить выбранные"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Админка для комментариев
    """

    list_display = [
        "id",
        "author_name",
        "content_short",
        "parent_object",
        "is_approved",
        "is_deleted_status",
        "deleted_info",
        "created_at_short",
    ]

    list_filter = ["is_approved", "is_deleted", "content_type", "created_at"]

    search_fields = ["author_name", "content"]

    readonly_fields = [
        "created_at",
        "updated_at",
        "content_type",
        "object_id",
        "content_object_link",
        "parent_link",
        "deleted_by",
        "deleted_at",
    ]

    fieldsets = [
        ("Автор", {"fields": ["author_name"]}),
        ("Комментарий", {"fields": ["content"]}),
        ("Привязка", {"fields": ["content_object_link", "parent_link"]}),
        (
            "Модерация",
            {"fields": ["is_approved", "is_deleted", "deleted_by", "deleted_at"]},
        ),
        ("Даты", {"fields": ["created_at", "updated_at"], "classes": ["collapse"]}),
    ]

    list_per_page = 50
    date_hierarchy = "created_at"

    actions = ["approve_comments", "soft_delete_comments", "restore_comments"]

    def content_short(self, obj):
        if obj.is_deleted:
            return mark_safe('<span style="color: #999;">[УДАЛЕН]</span>')
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_short.short_description = "Комментарий"

    def is_deleted_status(self, obj):
        if obj.is_deleted:
            return mark_safe(
                '<span style="color: red; font-weight: bold;">✓ Удален</span>'
            )
        return mark_safe('<span style="color: green;">✗ Активен</span>')

    is_deleted_status.short_description = "Статус удаления"
    is_deleted_status.admin_order_field = "is_deleted"

    def deleted_info(self, obj):
        if obj.is_deleted and obj.deleted_by:
            return f"Удален: {obj.deleted_by.username} ({obj.deleted_at.strftime('%d.%m.%Y %H:%M')})"
        elif obj.is_deleted:
            return "Удален (неизвестно кем)"
        return mark_safe("—")

    deleted_info.short_description = "Информация об удалении"

    def parent_object(self, obj):
        """К какому объекту комментарий"""
        if obj.is_deleted:
            return mark_safe('<span style="color: #999;">[УДАЛЕН]</span>')
        if obj.content_object:
            if hasattr(obj.content_object, "title"):
                return f"{obj.content_type.name}: {obj.content_object.title[:30]}..."
            elif hasattr(obj.content_object, "content"):
                return f"{obj.content_type.name}: {obj.content_object.content[:30]}..."
            return str(obj.content_object)
        return mark_safe("—")

    parent_object.short_description = "Объект"

    def content_object_link(self, obj):
        if obj.content_object:
            url = f"/admin/questions/{obj.content_type.model}/{obj.object_id}/change/"
            return format_html('<a href="{}">{}</a>', url, str(obj.content_object))
        return mark_safe("—")

    content_object_link.short_description = "Ссылка на объект"

    def parent_link(self, obj):
        if obj.parent:
            url = f"/admin/questions/comment/{obj.parent.id}/change/"
            return format_html('<a href="{}">Ответ на #{}</a>', url, obj.parent.id)
        return mark_safe("—")

    parent_link.short_description = "Родитель"

    def created_at_short(self, obj):
        return obj.created_at.strftime("%d.%m.%Y %H:%M")

    created_at_short.short_description = "Создано"

    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} комментариев одобрены")

    approve_comments.short_description = "Одобрить комментарии"

    def soft_delete_comments(self, request, queryset):
        updated = queryset.update(
            is_deleted=True, deleted_by=request.user, deleted_at=timezone.now()
        )
        self.message_user(request, f"{updated} комментариев помечены как удаленные")

    soft_delete_comments.short_description = "Мягкое удаление"

    def restore_comments(self, request, queryset):
        updated = queryset.update(is_deleted=False, deleted_by=None, deleted_at=None)
        self.message_user(request, f"{updated} комментариев восстановлены")

    restore_comments.short_description = "Восстановить комментарии"


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    """
    Админка для голосов (только просмотр)
    """

    list_display = [
        "id",
        "vote_display",
        "suggestion_link",
        "voter_session_short",
        "created_at",
    ]

    list_filter = ["vote", "created_at"]

    search_fields = ["voter_session"]

    readonly_fields = ["suggestion", "voter_session", "vote", "created_at"]

    list_per_page = 100

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def vote_display(self, obj):
        return "+" if obj.vote == 1 else "-"

    vote_display.short_description = "Голос"

    def suggestion_link(self, obj):
        return format_html(
            '<a href="/admin/questions/suggestion/{}/change/">Предложение #{}</a>',
            obj.suggestion.id,
            obj.suggestion.id,
        )

    suggestion_link.short_description = "Предложение"

    def voter_session_short(self, obj):
        return obj.voter_session[:15] + "..."

    voter_session_short.short_description = "Сессия"
