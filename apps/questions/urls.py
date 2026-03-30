from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api  # импортируем api

# API роутер
router = DefaultRouter()
router.register(r"questions", api.QuestionViewSet, basename="question")
router.register(r"suggestions", api.SuggestionViewSet, basename="suggestion")
router.register(r"comments", api.CommentViewSet, basename="comment")

urlpatterns = [
    # HTML страницы
    path("", views.home, name="home"),
    path("ask/", views.ask_question, name="ask_question"),
    path("question/<int:pk>/", views.question_detail, name="question_detail"),
    # Загрузка изображений для CKEditor (без проверки прав)
    path("ckeditor/upload/", views.upload_ckeditor_image, name="ckeditor_upload"),
    # API endpoints
    path("api/", include(router.urls)),
    # Дополнительные API эндпоинты
    path(
        "api/questions/<int:pk>/suggestions/",
        api.QuestionViewSet.as_view({"post": "add_suggestion"}),
        name="api-question-suggestions",
    ),
    path(
        "api/questions/<int:question_pk>/comments/",
        api.CommentViewSet.as_view({"post": "create"}),
        name="api-question-comments",
    ),
    path(
        "api/suggestions/<int:pk>/comments/",
        api.SuggestionViewSet.as_view({"post": "add_comment"}),
        name="api-suggestion-comments",
    ),
    path(
        "api/suggestions/<int:pk>/vote/",
        api.SuggestionViewSet.as_view({"post": "vote"}),
        name="api-suggestion-vote",
    ),
    path(
        "api/suggestions/<int:pk>/mark-best/",
        api.SuggestionViewSet.as_view({"post": "mark_as_best"}),
        name="api-suggestion-mark-best",
    ),
]
