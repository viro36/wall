import pytest
from apps.questions.forms import QuestionForm, SuggestionForm, CommentForm


@pytest.mark.django_db
class TestQuestionForm:
    """Тесты для формы вопроса"""

    def test_valid_question_form(self, organization):
        form_data = {
            "author_name": "Тестовый автор",
            "title": "Тестовый вопрос",
            "content": "Тестовое содержание вопроса",
            "organization": organization.id,
        }
        form = QuestionForm(data=form_data)
        assert form.is_valid()

    def test_invalid_question_form_missing_fields(self):
        form_data = {}
        form = QuestionForm(data=form_data)
        assert not form.is_valid()
        assert "author_name" in form.errors
        assert "title" in form.errors
        assert "content" in form.errors

    def test_question_form_district_field(self, district):
        form = QuestionForm()
        assert "district" in form.fields
        assert form.fields["district"].queryset.count() >= 0


@pytest.mark.django_db
class TestSuggestionForm:
    """Тесты для формы предложения"""

    def test_valid_suggestion_form(self):
        form_data = {
            "author_name": "Автор предложения",
            "content": "Тестовое содержание предложения",
        }
        form = SuggestionForm(data=form_data)
        assert form.is_valid()

    def test_invalid_suggestion_form_missing_fields(self):
        form_data = {}
        form = SuggestionForm(data=form_data)
        assert not form.is_valid()
        assert "author_name" in form.errors
        assert "content" in form.errors


@pytest.mark.django_db
class TestCommentForm:
    """Тесты для формы комментария"""

    def test_valid_comment_form(self):
        form_data = {"author_name": "Комментатор", "content": "Тестовый комментарий"}
        form = CommentForm(data=form_data)
        assert form.is_valid()

    def test_invalid_comment_form_missing_fields(self):
        form_data = {}
        form = CommentForm(data=form_data)
        assert not form.is_valid()
        assert "author_name" in form.errors
        assert "content" in form.errors
