import sys

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils import timezone

from .models import Question, Suggestion, Comment, Vote
from .serializers import (
    QuestionListSerializer,
    QuestionDetailSerializer,
    QuestionCreateSerializer,
    SuggestionListSerializer,
    SuggestionDetailSerializer,
    SuggestionCreateSerializer,
    CommentSerializer,
    VoteSerializer,
)


class QuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet для вопросов
    """

    queryset = (
        Question.objects.select_related(
            "organization__district", "organization__organization_type", "processed_by"
        )
        .prefetch_related("suggestions", "comments")
        .all()
    )

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "status",
        "is_approved",
        "organization",
        "organization__district",
        "organization__organization_type",
    ]
    search_fields = ["title", "content", "author_name"]
    ordering_fields = ["created_at", "views_count", "suggestions_count"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == "list":
            return QuestionListSerializer
        elif self.action == "retrieve":
            return QuestionDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return QuestionCreateSerializer
        return QuestionListSerializer

    def get_permissions(self):
        """Права доступа"""
        if self.action == "create":
            # Создание вопроса разрешено всем
            permission_classes = [permissions.AllowAny]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Изменение и удаление - только для авторизованных
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Просмотр - всем
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["post"])
    def add_suggestion(self, request, pk=None):
        """Добавить предложение к вопросу"""
        question = self.get_object()

        # Проверяем, можно ли добавлять предложения
        if question.status in ["closed"]:
            return Response(
                {"error": "Вопрос закрыт для новых предложений"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SuggestionCreateSerializer(
            data=request.data, context={"request": request, "view": self}
        )

        if serializer.is_valid():
            try:
                suggestion = serializer.save()

                # Обновляем статус вопроса
                if question.status == "new":
                    question.status = "has_suggestions"
                    question.save()

                # Увеличиваем счетчик предложений
                question.suggestions_count += 1
                question.save(update_fields=["suggestions_count"])

                # Для HTMX запросов возвращаем HTML
                if request.headers.get("HX-Request"):
                    html = render_to_string(
                        "questions/partials/suggestion_item.html",
                        {"suggestion": suggestion},
                    )

                    return HttpResponse(html, status=201, content_type="text/html")

                # Для обычных API запросов возвращаем JSON
                return Response(
                    SuggestionDetailSerializer(suggestion).data,
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                print(f"!!! EXCEPTION: {str(e)}", file=sys.stderr)
                import traceback

                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def add_comment(self, request, pk=None):
        """Добавить комментарий к вопросу"""
        question = self.get_object()

        serializer = CommentSerializer(data=request.data)

        if serializer.is_valid():
            comment = serializer.save(
                content_object=question,
                author_name=request.data.get("author_name", "Аноним"),
            )
            return Response(
                CommentSerializer(comment).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def take_in_processing(self, request, pk=None):
        """Взять вопрос в обработку (для админов)"""
        if not request.user.is_staff:
            return Response(
                {"error": "Только администраторы могут выполнять это действие"},
                status=status.HTTP_403_FORBIDDEN,
            )

        question = self.get_object()
        question.status = "processing"
        question.processed_by = request.user
        question.processed_at = timezone.now()
        question.save()

        # Возвращаем HTML для обновления кнопки
        html = f"""
        <div id="processing-controls">
            <button class="btn btn-warning" disabled>
                <i class="fa-solid fa-check me-2"></i>В обработке
            </button>
            <small class="text-muted ms-2">
                (взято {request.user.username} {timezone.now().strftime("%d.%m.%Y %H:%M")})
            </small>
        </div>
        """

        return HttpResponse(html)


class SuggestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet для предложений
    """

    queryset = (
        Suggestion.objects.select_related("question", "marked_by")
        .prefetch_related("comments", "votes")
        .all()
    )

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["question", "is_best", "is_approved"]
    ordering_fields = ["created_at", "likes_count"]
    ordering = ["-is_best", "-likes_count", "created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return SuggestionListSerializer
        elif self.action == "retrieve":
            return SuggestionDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return SuggestionCreateSerializer
        return SuggestionListSerializer

    def get_permissions(self):
        """Права доступа для предложений"""
        if self.action in ["create", "vote", "add_comment"]:
            # Создание предложений, голосование и комментарии разрешены всем
            permission_classes = [permissions.AllowAny]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Изменение и удаление - только для авторизованных
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Просмотр - всем
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["post"])
    def vote(self, request, pk=None):
        """Голосовать за предложение"""
        suggestion = self.get_object()

        # Получаем значение голоса из request.data
        vote_value = request.data.get("vote")

        # Преобразуем в int если это строка
        try:
            vote_value = int(vote_value)
        except (TypeError, ValueError):
            return Response(
                {"error": "Неверное значение голоса"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if vote_value not in [1, -1]:
            return Response(
                {"error": "Голос должен быть 1 или -1"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Получаем или создаем сессию
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

        # Проверяем существующий голос
        existing_vote = Vote.objects.filter(
            suggestion=suggestion, voter_session=session_key
        ).first()

        if existing_vote:
            if existing_vote.vote == vote_value:
                # Отмена голоса
                existing_vote.delete()
            else:
                # Изменение голоса
                existing_vote.vote = vote_value
                existing_vote.save()
        else:
            # Новый голос
            Vote.objects.create(
                suggestion=suggestion, voter_session=session_key, vote=vote_value
            )

        # Обновляем счетчики
        suggestion.update_votes_count()

        # Для HTMX запросов возвращаем HTML с обновленными счетчиками
        if request.headers.get("HX-Request"):
            html = f"""
            <div class="vote-stats" id="vote-stats-{suggestion.id}">
                <span class="vote-count likes-count">{suggestion.likes_count}</span>
                <span class="vote-separator">/</span>
                <span class="vote-count dislikes-count">{suggestion.dislikes_count}</span>
            </div>
            """
            return HttpResponse(html, content_type="text/html")

        # Для обычных API запросов
        return Response(
            {
                "likes_count": suggestion.likes_count,
                "dislikes_count": suggestion.dislikes_count,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def add_comment(self, request, pk=None):
        """Добавить комментарий к предложению"""
        suggestion = self.get_object()

        # Получаем данные из запроса
        author_name = request.data.get("author_name")
        content = request.data.get("content")
        parent_id = request.data.get("parent")

        print(f"Creating comment for suggestion {suggestion.id}")
        print(f"author_name: {author_name}")
        print(f"content: {content}")
        print(f"parent_id: {parent_id}")

        if not author_name or not content:
            return Response(
                {"error": "Имя и текст комментария обязательны"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Получаем ContentType для Suggestion
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(Suggestion)
        print(f"content_type_id: {content_type.id}")
        print(f"object_id: {suggestion.id}")

        try:
            # Создаем комментарий
            comment = Comment.objects.create(
                content_type=content_type,
                object_id=suggestion.id,
                author_name=author_name,
                content=content,
                parent_id=parent_id if parent_id else None,
                is_approved=True,
            )
            print(f"Comment created with ID: {comment.id}")

            # Для HTMX запросов возвращаем HTML комментария
            if request.headers.get("HX-Request"):
                html = render_to_string(
                    "questions/partials/comment_item.html",
                    {"comment": comment, "suggestion": suggestion},
                )
                return HttpResponse(html, status=201, content_type="text/html")

            # Для обычных API запросов возвращаем JSON
            return Response(
                CommentSerializer(comment).data, status=status.HTTP_201_CREATED
            )
        except Exception as e:
            print(f"Error creating comment: {str(e)}")
            import traceback

            traceback.print_exc()
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def mark_as_best(self, request, pk=None):
        """Отметить как лучшее предложение (для админов)"""
        if not request.user.is_staff:
            return Response(
                {"error": "Только администраторы могут выполнять это действие"},
                status=status.HTTP_403_FORBIDDEN,
            )

        suggestion = self.get_object()

        # Снимаем отметку "лучшее" со всех других предложений этого вопроса
        Suggestion.objects.filter(question=suggestion.question).update(is_best=False)

        # Отмечаем текущее как лучшее
        suggestion.is_best = True
        suggestion.marked_as_best_at = timezone.now()
        suggestion.marked_by = request.user
        suggestion.save()

        # Обновляем статус вопроса
        question = suggestion.question
        question.status = "has_best"
        question.save()

        # Для HTMX запросов возвращаем весь список предложений
        if request.headers.get("HX-Request"):
            suggestions = question.suggestions.all()
            html = render_to_string(
                "questions/partials/suggestions_list.html",
                {"suggestions": suggestions, "user": request.user},
            )
            return HttpResponse(html, status=200, content_type="text/html")

        return Response({"status": "suggestion marked as best"})


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для комментариев
    """

    queryset = Comment.objects.select_related("content_type", "parent").all()

    serializer_class = CommentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["content_type", "object_id", "is_approved", "is_deleted"]
    ordering_fields = ["created_at"]
    ordering = ["created_at"]

    def get_queryset(self):
        """Фильтр по родительскому объекту и показываем только не удаленные"""
        queryset = super().get_queryset()

        # По умолчанию показываем только не удаленные
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_deleted=False)

        # Фильтр по вопросу
        question_id = self.request.query_params.get("question")
        if question_id:
            content_type = ContentType.objects.get_for_model(Question)
            queryset = queryset.filter(content_type=content_type, object_id=question_id)

        # Фильтр по предложению
        suggestion_id = self.request.query_params.get("suggestion")
        if suggestion_id:
            content_type = ContentType.objects.get_for_model(Suggestion)
            queryset = queryset.filter(
                content_type=content_type, object_id=suggestion_id
            )

        return queryset
