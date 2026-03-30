import pytest
from django.urls import reverse
from rest_framework import status
from apps.questions.models import Question, Suggestion, Comment, Vote


@pytest.mark.django_db
class TestQuestionAPI:
    """Тесты API для вопросов"""

    def test_list_questions(self, api_client, question):
        url = reverse("question-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_retrieve_question(self, api_client, question):
        url = reverse("question-detail", args=[question.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == question.title
        assert response.data["author_name"] == question.author_name

    def test_create_question(self, api_client, organization):
        url = reverse("question-list")
        data = {
            "author_name": "Новый автор",
            "title": "Новый вопрос",
            "content": "Содержание нового вопроса",
            "organization": organization.id,
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Question.objects.count() >= 1

    def test_add_suggestion_to_question(self, api_client, question):
        url = reverse("api-question-suggestions", args=[question.id])
        data = {"author_name": "Автор предложения", "content": "Тестовое предложение"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert question.suggestions.count() == 1


@pytest.mark.django_db
class TestSuggestionAPI:
    """Тесты API для предложений"""

    def test_list_suggestions(self, api_client, suggestion):
        url = reverse("suggestion-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_retrieve_suggestion(self, api_client, suggestion):
        url = reverse("suggestion-detail", args=[suggestion.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["author_name"] == suggestion.author_name
        assert response.data["content"] == suggestion.content

    def test_vote_for_suggestion(self, api_client, suggestion):
        url = reverse("api-suggestion-vote", args=[suggestion.id])
        data = {"vote": 1}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        suggestion.refresh_from_db()
        assert suggestion.likes_count == 1

    def test_change_vote(self, api_client, suggestion):
        # Сначала ставим лайк
        url = reverse("api-suggestion-vote", args=[suggestion.id])
        api_client.post(url, {"vote": 1}, format="json")
        suggestion.refresh_from_db()
        assert suggestion.likes_count == 1

        # Меняем на дизлайк
        api_client.post(url, {"vote": -1}, format="json")
        suggestion.refresh_from_db()
        assert suggestion.likes_count == 0
        assert suggestion.dislikes_count == 1

    def test_mark_as_best_by_admin(self, api_client, suggestion, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = reverse("api-suggestion-mark-best", args=[suggestion.id])
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        suggestion.refresh_from_db()
        assert suggestion.is_best is True
        assert suggestion.question.status == "has_best"

    def test_mark_as_best_by_regular_user(self, api_client, suggestion, regular_user):
        api_client.force_authenticate(user=regular_user)
        url = reverse("api-suggestion-mark-best", args=[suggestion.id])
        response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCommentAPI:
    """Тесты API для комментариев"""

    def test_add_comment_to_suggestion(self, api_client, suggestion):
        url = reverse("api-suggestion-comments", args=[suggestion.id])
        data = {"author_name": "Комментатор", "content": "Тестовый комментарий"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert suggestion.comments.count() == 1

    def test_reply_to_comment(self, api_client, suggestion, comment):
        url = reverse("api-suggestion-comments", args=[suggestion.id])
        data = {
            "author_name": "Ответчик",
            "content": "Тестовый ответ",
            "parent": comment.id,
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert comment.replies.count() == 1
