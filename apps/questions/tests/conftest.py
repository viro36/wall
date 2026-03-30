import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from apps.organizations.models import District, OrganizationType, Organization
from apps.questions.models import Question, Suggestion, Comment, Vote


@pytest.fixture
def api_client():
    """Клиент для API тестов"""
    return APIClient()


@pytest.fixture
def client():
    """Обычный клиент для тестов"""
    from django.test import Client

    return Client()


@pytest.fixture
def admin_user(db):
    """Фикстура администратора"""
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="admin123"
    )


@pytest.fixture
def regular_user(db):
    """Фикстура обычного пользователя"""
    return User.objects.create_user(
        username="user", email="user@example.com", password="user123"
    )


@pytest.fixture
def district(db):
    """Фикстура района"""
    return District.objects.create(full_name="Тестовый район", short_name="Тест район")


@pytest.fixture
def organization_type(db):
    """Фикстура типа организации"""
    return OrganizationType.objects.create(name="Тестовый тип организации")


@pytest.fixture
def organization(db, district, organization_type):
    """Фикстура организации"""
    return Organization.objects.create(
        inn="1234567890",
        kpp="123456789",
        ogrn="1234567890123",
        full_name="Тестовая организация полное название",
        short_name="Тест Org",
        address_raw="г. Тестовый, ул. Тестовая, д. 1",
        postal_code="123456",
        region="Тестовая область",
        city="Тестовый город",
        street="Тестовая улица",
        house="1",
        coordinates="55.7558, 37.6176",
        status="ACTIVE",
        district=district,
        organization_type=organization_type,
    )


@pytest.fixture
def question(db, organization):
    """Фикстура вопроса"""
    return Question.objects.create(
        author_name="Тестовый автор",
        title="Тестовый вопрос",
        content="Тестовое содержание вопроса",
        organization=organization,
        status="new",
        is_approved=True,
    )


@pytest.fixture
def question_with_suggestions(db, question):
    """Фикстура вопроса с предложениями"""
    for i in range(3):
        Suggestion.objects.create(
            question=question,
            author_name=f"Автор {i}",
            content=f"Тестовое предложение {i}",
            is_approved=True,
        )
    return question


@pytest.fixture
def suggestion(db, question):
    """Фикстура предложения"""
    return Suggestion.objects.create(
        question=question,
        author_name="Автор предложения",
        content="Тестовое содержание предложения",
        is_approved=True,
    )


@pytest.fixture
def suggestion_with_votes(db, suggestion):
    """Фикстура предложения с голосами"""
    session_key = "test_session_key"

    # Добавляем лайки
    for i in range(5):
        Vote.objects.create(
            suggestion=suggestion, voter_session=f"{session_key}_{i}_like", vote=1
        )

    # Добавляем дизлайки
    for i in range(3):
        Vote.objects.create(
            suggestion=suggestion, voter_session=f"{session_key}_{i}_dislike", vote=-1
        )

    suggestion.update_votes_count()
    return suggestion


@pytest.fixture
def comment(db, suggestion):
    """Фикстура комментария"""
    content_type = ContentType.objects.get_for_model(Suggestion)
    return Comment.objects.create(
        content_type=content_type,
        object_id=suggestion.id,
        author_name="Автор комментария",
        content="Тестовый комментарий",
        is_approved=True,
    )


@pytest.fixture
def comment_with_replies(db, suggestion):
    """Фикстура комментария с ответами"""
    content_type = ContentType.objects.get_for_model(Suggestion)

    parent = Comment.objects.create(
        content_type=content_type,
        object_id=suggestion.id,
        author_name="Родительский комментарий",
        content="Тестовый родительский комментарий",
        is_approved=True,
    )

    for i in range(2):
        Comment.objects.create(
            content_type=content_type,
            object_id=suggestion.id,
            author_name=f"Ответ {i}",
            content=f"Тестовый ответ {i}",
            parent=parent,
            is_approved=True,
        )

    return parent


@pytest.fixture
def vote(suggestion):
    return Vote.objects.create(
        suggestion=suggestion, voter_session="test_session_12345", vote=1
    )
