import pytest
from django.utils import timezone
from apps.questions.models import Vote


@pytest.mark.django_db
class TestQuestionModel:
    """Тесты для модели Question"""

    def test_create_question(self, question, organization):
        assert question.author_name == "Тестовый автор"
        assert question.title == "Тестовый вопрос"
        assert question.content == "Тестовое содержание вопроса"
        assert question.organization == organization
        assert question.status == "new"
        assert question.views_count == 0
        assert question.suggestions_count == 0
        assert question.is_approved is True

    def test_question_str(self, question):
        expected = f"{question.title[:50]}... ({question.author_name})"
        assert str(question) == expected

    def test_question_status_choices(self, question):
        assert question.get_status_display() == "Новый"

        question.status = "processing"
        question.save()
        assert question.get_status_display() == "В обработке"

        question.status = "has_suggestions"
        question.save()
        assert question.get_status_display() == "Есть предложения"

        question.status = "has_best"
        question.save()
        assert question.get_status_display() == "Есть лучшее"

        question.status = "closed"
        question.save()
        assert question.get_status_display() == "Закрыт"

    def test_question_view_count_increment(self, question):
        initial_views = question.views_count
        question.views_count += 1
        question.save()
        question.refresh_from_db()
        assert question.views_count == initial_views + 1


@pytest.mark.django_db
class TestSuggestionModel:
    """Тесты для модели Suggestion"""

    def test_create_suggestion(self, suggestion, question):
        assert suggestion.author_name == "Автор предложения"
        assert suggestion.content == "Тестовое содержание предложения"
        assert suggestion.question == question
        assert suggestion.is_best is False
        assert suggestion.likes_count == 0
        assert suggestion.dislikes_count == 0

    def test_suggestion_str(self, suggestion):
        expected = f"Предложение к {suggestion.question.id} от {suggestion.author_name}"
        assert str(suggestion) == expected

    def test_mark_as_best(self, suggestion, admin_user):
        assert suggestion.is_best is False

        suggestion.is_best = True
        suggestion.marked_by = admin_user
        suggestion.marked_as_best_at = timezone.now()
        suggestion.save()

        suggestion.refresh_from_db()
        assert suggestion.is_best is True
        assert suggestion.marked_by == admin_user
        assert suggestion.marked_as_best_at is not None

    def test_update_votes_count(self, suggestion_with_votes):
        suggestion = suggestion_with_votes
        assert suggestion.likes_count == 5
        assert suggestion.dislikes_count == 3


@pytest.mark.django_db
class TestCommentModel:
    """Тесты для модели Comment"""

    def test_create_comment(self, comment, suggestion):
        assert comment.author_name == "Автор комментария"
        assert comment.content == "Тестовый комментарий"
        assert comment.content_object == suggestion
        assert comment.parent is None
        assert comment.is_approved is True
        assert comment.is_deleted is False

    def test_comment_str(self, comment):
        expected = f"Комментарий от {comment.author_name} к {comment.content_object}"
        assert str(comment) == expected

    def test_is_reply_property(self, comment_with_replies):
        parent = comment_with_replies
        assert parent.is_reply is False

        reply = parent.replies.first()
        assert reply.is_reply is True

    def test_soft_delete(self, comment, admin_user):
        assert comment.is_deleted is False

        comment.is_deleted = True
        comment.deleted_by = admin_user
        comment.deleted_at = timezone.now()
        comment.save()

        comment.refresh_from_db()
        assert comment.is_deleted is True
        assert comment.deleted_by == admin_user
        assert comment.deleted_at is not None


@pytest.mark.django_db
class TestVoteModel:
    """Тесты для модели Vote"""

    def test_create_vote(self, suggestion):
        vote = Vote.objects.create(
            suggestion=suggestion, voter_session="test_session", vote=1
        )

        assert vote.suggestion == suggestion
        assert vote.voter_session == "test_session"
        assert vote.vote == 1

    def test_vote_unique_constraint(self, suggestion):
        Vote.objects.create(suggestion=suggestion, voter_session="test_session", vote=1)

        # Попытка создать второй голос с той же сессией должна вызвать ошибку
        with pytest.raises(Exception):
            Vote.objects.create(
                suggestion=suggestion, voter_session="test_session", vote=-1
            )

    def test_vote_str(self, suggestion):
        vote = Vote.objects.create(
            suggestion=suggestion, voter_session="test_session", vote=1
        )
        expected = f"+ от сессии test_ses..."
        assert str(vote) == expected[: len(str(vote))]
