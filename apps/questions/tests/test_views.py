import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestQuestionViews:
    """Тесты для view функций"""

    def test_home_page(self, client, question):
        url = reverse("home")
        response = client.get(url)

        assert response.status_code == 200
        assert "questions/home.html" in [t.name for t in response.templates]
        assert "questions" in response.context

    def test_question_detail_page(self, client, question):
        url = reverse("question_detail", args=[question.id])
        response = client.get(url)

        assert response.status_code == 200
        assert "questions/question_detail.html" in [t.name for t in response.templates]
        assert response.context["question"] == question

    def test_ask_question_page_get(self, client):
        url = reverse("ask_question")
        response = client.get(url)

        assert response.status_code == 200
        assert "questions/ask_question.html" in [t.name for t in response.templates]
        assert "form" in response.context

    def test_ask_question_page_post(self, client, organization):
        url = reverse("ask_question")
        data = {
            "author_name": "Тестовый автор",
            "title": "Тестовый вопрос",
            "content": "Тестовое содержание",
            "organization": organization.id,
        }
        response = client.post(url, data)

        assert response.status_code == 302  # Redirect
