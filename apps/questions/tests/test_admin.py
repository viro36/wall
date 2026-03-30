import pytest
from unittest.mock import patch
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.utils import timezone
from django.test import RequestFactory
from apps.questions.admin import QuestionAdmin, SuggestionAdmin, CommentAdmin, VoteAdmin
from apps.questions.models import Question, Suggestion, Comment, Vote


def get_request(user=None):
    """Create a request with user and a fake session."""
    factory = RequestFactory()
    request = factory.get("/admin/")
    request.user = user or User.objects.create_superuser(
        "admin", "admin@example.com", "password"
    )
    # Add a dummy session attribute to avoid session middleware error
    request.session = {}
    return request


@pytest.mark.django_db
class TestQuestionAdmin:
    """Тесты для админки вопросов"""

    def test_question_admin_list_display(self):
        site = AdminSite()
        admin = QuestionAdmin(Question, site)

        expected_fields = [
            "id",
            "title_short",
            "author_name",
            "organization_info",
            "status_colored",
            "suggestions_count",
            "views_count",
            "created_at_short",
        ]
        for field in expected_fields:
            assert field in admin.list_display

    def test_question_admin_list_filter(self):
        site = AdminSite()
        admin = QuestionAdmin(Question, site)

        expected_filters = [
            "status",
            "is_approved",
            "organization__district",
            "organization__organization_type",
            "created_at",
        ]
        for filter_name in expected_filters:
            assert filter_name in admin.list_filter

    def test_question_admin_search_fields(self):
        site = AdminSite()
        admin = QuestionAdmin(Question, site)

        expected_fields = ["title", "content", "author_name", "author_email"]
        for field in expected_fields:
            assert field in admin.search_fields

    def test_question_admin_readonly_fields(self):
        site = AdminSite()
        admin = QuestionAdmin(Question, site)

        expected_fields = [
            "created_at",
            "updated_at",
            "status_changed_at",
            "processed_at",
            "suggestions_count",
            "views_count",
            "comments_link",
        ]
        for field in expected_fields:
            assert field in admin.readonly_fields

    def test_question_admin_actions(self):
        site = AdminSite()
        admin = QuestionAdmin(Question, site)
        request = get_request()
        actions = admin.get_actions(request)
        action_names = list(actions.keys())  # Get action names directly
        expected_actions = [
            "mark_as_processing",
            "mark_as_has_best",
            "mark_as_closed",
            "approve_questions",
        ]
        for action in expected_actions:
            assert action in action_names

    def test_title_short_method(self, admin_user, question):
        site = AdminSite()
        admin = QuestionAdmin(Question, site)

        result = admin.title_short(question)
        if len(question.title) > 50:
            assert result == question.title[:50] + "..."
        else:
            assert result == question.title

    def test_organization_info_method(self, admin_user, question):
        site = AdminSite()
        admin = QuestionAdmin(Question, site)

        result = admin.organization_info(question)
        if question.organization:
            assert question.organization.short_name in result
        else:
            assert result == "-"

    def test_status_colored_method(self, admin_user, question):
        site = AdminSite()
        admin = QuestionAdmin(Question, site)

        result = admin.status_colored(question)
        assert '<span style="color:' in result
        assert question.get_status_display() in result

    def test_created_at_short_method(self, admin_user, question):
        site = AdminSite()
        admin = QuestionAdmin(Question, site)

        result = admin.created_at_short(question)
        assert result == question.created_at.strftime("%d.%m.%Y %H:%M")

    @patch.object(QuestionAdmin, "message_user", return_value=None)
    def test_mark_as_processing_action(self, mock_message, admin_user, question):
        site = AdminSite()
        admin = QuestionAdmin(Question, site)
        request = get_request(admin_user)

        queryset = Question.objects.filter(id=question.id)
        admin.mark_as_processing(request, queryset)

        question.refresh_from_db()
        assert question.status == "processing"
        assert question.processed_at is not None
        assert question.processed_by == admin_user

    @patch.object(QuestionAdmin, "message_user", return_value=None)
    def test_mark_as_has_best_action(self, mock_message, admin_user, question):
        site = AdminSite()
        admin = QuestionAdmin(Question, site)
        request = get_request(admin_user)

        queryset = Question.objects.filter(id=question.id)
        admin.mark_as_has_best(request, queryset)

        question.refresh_from_db()
        assert question.status == "has_best"

    @patch.object(QuestionAdmin, "message_user", return_value=None)
    def test_mark_as_closed_action(self, mock_message, admin_user, question):
        site = AdminSite()
        admin = QuestionAdmin(Question, site)
        request = get_request(admin_user)

        queryset = Question.objects.filter(id=question.id)
        admin.mark_as_closed(request, queryset)

        question.refresh_from_db()
        assert question.status == "closed"

    @patch.object(QuestionAdmin, "message_user", return_value=None)
    def test_approve_questions_action(self, mock_message, admin_user, question):
        site = AdminSite()
        admin = QuestionAdmin(Question, site)
        request = get_request(admin_user)

        # Сначала делаем вопрос неодобренным
        question.is_approved = False
        question.save()

        queryset = Question.objects.filter(id=question.id)
        admin.approve_questions(request, queryset)

        question.refresh_from_db()
        assert question.is_approved is True


@pytest.mark.django_db
class TestSuggestionAdmin:
    """Тесты для админки предложений"""

    def test_suggestion_admin_list_display(self):
        site = AdminSite()
        admin = SuggestionAdmin(Suggestion, site)

        expected_fields = [
            "id",
            "question_link",
            "author_name",
            "content_short",
            "votes_display",
            "is_best_colored",
            "created_at_short",
        ]
        for field in expected_fields:
            assert field in admin.list_display

    def test_suggestion_admin_list_filter(self):
        site = AdminSite()
        admin = SuggestionAdmin(Suggestion, site)

        expected_filters = ["is_best", "is_approved", "created_at"]
        for filter_name in expected_filters:
            assert filter_name in admin.list_filter

    def test_suggestion_admin_search_fields(self):
        site = AdminSite()
        admin = SuggestionAdmin(Suggestion, site)

        expected_fields = ["content", "author_name", "author_email"]
        for field in expected_fields:
            assert field in admin.search_fields

    def test_suggestion_admin_actions(self):
        site = AdminSite()
        admin = SuggestionAdmin(Suggestion, site)
        request = get_request()
        actions = admin.get_actions(request)
        action_names = list(actions.keys())  # Get action names directly
        expected_actions = ["mark_as_best", "unmark_as_best", "approve_suggestions"]
        for action in expected_actions:
            assert action in action_names

    def test_question_link_method(self, admin_user, suggestion):
        site = AdminSite()
        admin = SuggestionAdmin(Suggestion, site)

        result = admin.question_link(suggestion)
        assert f"Вопрос #{suggestion.question.id}" in result
        assert f"/admin/questions/question/{suggestion.question.id}/change/" in result

    def test_content_short_method(self, admin_user, suggestion):
        site = AdminSite()
        admin = SuggestionAdmin(Suggestion, site)

        result = admin.content_short(suggestion)
        if len(suggestion.content) > 75:
            assert result.endswith("...")
        else:
            assert result == suggestion.content

    def test_votes_display_method(self, admin_user, suggestion):
        site = AdminSite()
        admin = SuggestionAdmin(Suggestion, site)

        result = admin.votes_display(suggestion)
        assert f"+ {suggestion.likes_count} | - {suggestion.dislikes_count}" in result

    def test_is_best_colored_method(self, admin_user, suggestion):
        site = AdminSite()
        admin = SuggestionAdmin(Suggestion, site)

        suggestion.is_best = True
        result = admin.is_best_colored(suggestion)
        assert "Лучшее" in result
        assert "color: gold" in result

        suggestion.is_best = False
        result = admin.is_best_colored(suggestion)
        assert result == "—"

    @patch.object(SuggestionAdmin, "message_user", return_value=None)
    def test_mark_as_best_action(self, mock_message, admin_user, suggestion):
        site = AdminSite()
        admin = SuggestionAdmin(Suggestion, site)
        request = get_request(admin_user)

        queryset = Suggestion.objects.filter(id=suggestion.id)
        admin.mark_as_best(request, queryset)

        suggestion.refresh_from_db()
        assert suggestion.is_best is True
        assert suggestion.marked_as_best_at is not None
        assert suggestion.marked_by == admin_user
        assert suggestion.question.status == "has_best"

    @patch.object(SuggestionAdmin, "message_user", return_value=None)
    def test_unmark_as_best_action(self, mock_message, admin_user, suggestion):
        site = AdminSite()
        admin = SuggestionAdmin(Suggestion, site)
        request = get_request(admin_user)

        # Сначала отмечаем как лучшее
        suggestion.is_best = True
        suggestion.marked_as_best_at = timezone.now()
        suggestion.marked_by = admin_user
        suggestion.save()

        queryset = Suggestion.objects.filter(id=suggestion.id)
        admin.unmark_as_best(request, queryset)

        suggestion.refresh_from_db()
        assert suggestion.is_best is False
        assert suggestion.marked_as_best_at is None
        assert suggestion.marked_by is None

    @patch.object(SuggestionAdmin, "message_user", return_value=None)
    def test_approve_suggestions_action(self, mock_message, admin_user, suggestion):
        site = AdminSite()
        admin = SuggestionAdmin(Suggestion, site)
        request = get_request(admin_user)

        # Сначала делаем предложение неодобренным
        suggestion.is_approved = False
        suggestion.save()

        queryset = Suggestion.objects.filter(id=suggestion.id)
        admin.approve_suggestions(request, queryset)

        suggestion.refresh_from_db()
        assert suggestion.is_approved is True


@pytest.mark.django_db
class TestCommentAdmin:
    """Тесты для админки комментариев"""

    def test_comment_admin_list_display(self):
        site = AdminSite()
        admin = CommentAdmin(Comment, site)

        expected_fields = [
            "id",
            "author_name",
            "content_short",
            "parent_object",
            "is_approved",
            "is_deleted_status",
            "deleted_info",
            "created_at_short",
        ]
        for field in expected_fields:
            assert field in admin.list_display

    def test_comment_admin_list_filter(self):
        site = AdminSite()
        admin = CommentAdmin(Comment, site)

        expected_filters = ["is_approved", "is_deleted", "content_type", "created_at"]
        for filter_name in expected_filters:
            assert filter_name in admin.list_filter

    def test_comment_admin_search_fields(self):
        site = AdminSite()
        admin = CommentAdmin(Comment, site)

        expected_fields = ["author_name", "content"]
        for field in expected_fields:
            assert field in admin.search_fields

    def test_comment_admin_actions(self):
        site = AdminSite()
        admin = CommentAdmin(Comment, site)
        request = get_request()
        actions = admin.get_actions(request)
        action_names = list(actions.keys())  # Get action names directly
        expected_actions = [
            "approve_comments",
            "soft_delete_comments",
            "restore_comments",
        ]
        for action in expected_actions:
            assert action in action_names

    def test_content_short_method(self, admin_user, comment):
        site = AdminSite()
        admin = CommentAdmin(Comment, site)

        result = admin.content_short(comment)
        if len(comment.content) > 50:
            assert result.endswith("...")
        else:
            assert result == comment.content

    def test_is_deleted_status_method(self, admin_user, comment):
        site = AdminSite()
        admin = CommentAdmin(Comment, site)

        comment.is_deleted = False
        result = admin.is_deleted_status(comment)
        assert "Активен" in result
        assert "color: green" in result

        comment.is_deleted = True
        result = admin.is_deleted_status(comment)
        assert "Удален" in result
        assert "color: red" in result

    @patch.object(CommentAdmin, "message_user", return_value=None)
    def test_approve_comments_action(self, mock_message, admin_user, comment):
        site = AdminSite()
        admin = CommentAdmin(Comment, site)
        request = get_request(admin_user)

        # Сначала делаем комментарий неодобренным
        comment.is_approved = False
        comment.save()

        queryset = Comment.objects.filter(id=comment.id)
        admin.approve_comments(request, queryset)

        comment.refresh_from_db()
        assert comment.is_approved is True

    @patch.object(CommentAdmin, "message_user", return_value=None)
    def test_soft_delete_comments_action(self, mock_message, admin_user, comment):
        site = AdminSite()
        admin = CommentAdmin(Comment, site)
        request = get_request(admin_user)

        queryset = Comment.objects.filter(id=comment.id)
        admin.soft_delete_comments(request, queryset)

        comment.refresh_from_db()
        assert comment.is_deleted is True
        assert comment.deleted_by == admin_user
        assert comment.deleted_at is not None

    @patch.object(CommentAdmin, "message_user", return_value=None)
    def test_restore_comments_action(self, mock_message, admin_user, comment):
        site = AdminSite()
        admin = CommentAdmin(Comment, site)
        request = get_request(admin_user)

        # Сначала удаляем
        comment.is_deleted = True
        comment.deleted_by = admin_user
        comment.deleted_at = timezone.now()
        comment.save()

        queryset = Comment.objects.filter(id=comment.id)
        admin.restore_comments(request, queryset)

        comment.refresh_from_db()
        assert comment.is_deleted is False
        assert comment.deleted_by is None
        assert comment.deleted_at is None


@pytest.mark.django_db
class TestVoteAdmin:
    """Тесты для админки голосов"""

    def test_vote_admin_list_display(self):
        site = AdminSite()
        admin = VoteAdmin(Vote, site)

        expected_fields = [
            "id",
            "vote_display",
            "suggestion_link",
            "voter_session_short",
            "created_at",
        ]
        for field in expected_fields:
            assert field in admin.list_display

    def test_vote_admin_list_filter(self):
        site = AdminSite()
        admin = VoteAdmin(Vote, site)

        expected_filters = ["vote", "created_at"]
        for filter_name in expected_filters:
            assert filter_name in admin.list_filter

    def test_vote_admin_search_fields(self):
        site = AdminSite()
        admin = VoteAdmin(Vote, site)

        expected_fields = ["voter_session"]
        for field in expected_fields:
            assert field in admin.search_fields

    def test_has_add_permission(self):
        site = AdminSite()
        admin = VoteAdmin(Vote, site)

        assert admin.has_add_permission(None) is False

    def test_has_change_permission(self):
        site = AdminSite()
        admin = VoteAdmin(Vote, site)

        assert admin.has_change_permission(None) is False

    def test_vote_display_method(self, admin_user, vote):
        site = AdminSite()
        admin = VoteAdmin(Vote, site)

        result = admin.vote_display(vote)
        assert result == ("+" if vote.vote == 1 else "-")

    def test_voter_session_short_method(self, admin_user, vote):
        site = AdminSite()
        admin = VoteAdmin(Vote, site)

        result = admin.voter_session_short(vote)
        if len(vote.voter_session) > 15:
            assert len(result) <= 18
            assert result.endswith("...")
        else:
            assert result == vote.voter_session
