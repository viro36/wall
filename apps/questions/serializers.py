from rest_framework import serializers
from .models import Question, Suggestion, Comment, Vote


class CommentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для комментариев
    """

    author_name = serializers.CharField(max_length=255)
    is_reply = serializers.BooleanField(read_only=True)
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "author_name",
            "content",
            "parent",
            "is_approved",
            "is_reply",
            "replies_count",
            "created_at",
        ]
        read_only_fields = ["is_approved", "created_at"]

    def get_replies_count(self, obj):
        return obj.replies.count()

    def validate_parent(self, value):
        """Проверяем, что родительский комментарий принадлежит тому же объекту"""
        if value:
            if (
                value.content_type != self.instance.content_type
                or value.object_id != self.instance.object_id
            ):
                raise serializers.ValidationError(
                    "Родительский комментарий должен относиться к тому же объекту"
                )
        return value


class VoteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для голосов
    """

    vote_display = serializers.SerializerMethodField()

    class Meta:
        model = Vote
        fields = [
            "id",
            "suggestion",
            "vote",
            "vote_display",
            "created_at",
        ]
        read_only_fields = ["created_at"]
        extra_kwargs = {}

    def get_vote_display(self, obj):
        return "+" if obj.vote == 1 else "-"

    def validate_vote(self, value):
        """Проверяем только допустимые значения голоса"""
        if value not in [1, -1]:
            raise serializers.ValidationError("Голос должен быть 1 или -1")
        return value


class SuggestionListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка предложений
    """

    author_name = serializers.CharField(max_length=255)
    author_email = serializers.EmailField(allow_blank=True, required=False)
    vote_display = serializers.SerializerMethodField()
    comments_count = serializers.IntegerField(read_only=True)
    organization_name = serializers.CharField(
        source="organization.short_name", read_only=True, allow_null=True
    )
    district_name = serializers.CharField(
        source="organization.district.short_name", read_only=True, allow_null=True
    )

    class Meta:
        model = Suggestion
        fields = [
            "id",
            "author_name",
            "author_email",
            "content",
            "likes_count",
            "dislikes_count",
            "vote_display",
            "comments_count",
            "is_best",
            "is_approved",
            "organization",
            "organization_name",
            "district_name",
            "created_at",
        ]
        read_only_fields = [
            "likes_count",
            "dislikes_count",
            "is_best",
            "is_approved",
            "created_at",
        ]

    def get_vote_display(self, obj):
        """Возвращает соотношение лайков/дизлайков"""
        total = obj.likes_count + obj.dislikes_count
        if total == 0:
            return "0% +"
        likes_percent = (obj.likes_count / total) * 100
        return f"{likes_percent:.0f}% -"


class SuggestionDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для детального просмотра предложения
    """

    author_name = serializers.CharField(max_length=255)
    author_email = serializers.EmailField(allow_blank=True, required=False)
    comments = CommentSerializer(many=True, read_only=True)
    user_vote = serializers.SerializerMethodField()
    organization_detail = serializers.SerializerMethodField()

    class Meta:
        model = Suggestion
        fields = [
            "id",
            "question",
            "author_name",
            "author_email",
            "content",
            "likes_count",
            "dislikes_count",
            "reactions",
            "is_best",
            "is_approved",
            "comments",
            "user_vote",
            "organization",
            "organization_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "likes_count",
            "dislikes_count",
            "is_best",
            "is_approved",
            "created_at",
            "updated_at",
        ]

    def get_user_vote(self, obj):
        """Проверяет, голосовал ли текущий пользователь"""
        request = self.context.get("request")
        if request and request.session.session_key:
            try:
                vote = Vote.objects.get(
                    suggestion=obj, voter_session=request.session.session_key
                )
                return {"vote": vote.vote, "display": "+" if vote.vote == 1 else "-"}
            except Vote.DoesNotExist:
                pass
        return None

    def get_organization_detail(self, obj):
        """Детальная информация об организации"""
        if obj.organization:
            return {
                "id": obj.organization.id,
                "short_name": obj.organization.short_name,
                "full_name": obj.organization.full_name,
                "district": (
                    obj.organization.district.short_name
                    if obj.organization.district
                    else None
                ),
                "address": obj.organization.address_raw,
            }
        return None


class SuggestionCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания предложения
    """

    author_name = serializers.CharField(max_length=255)

    class Meta:
        model = Suggestion
        fields = [
            "author_name",
            "content",
            "organization",
        ]

    def create(self, validated_data):
        """Автоматически привязываем к вопросу"""
        question_id = self.context["view"].kwargs.get("pk")

        if not question_id:
            raise serializers.ValidationError("Question ID not found")

        validated_data["question_id"] = question_id

        return super().create(validated_data)


class QuestionListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка вопросов
    """

    author_name = serializers.CharField(max_length=255)
    author_email = serializers.EmailField(allow_blank=True, required=False)
    organization_name = serializers.CharField(
        source="organization.short_name", read_only=True
    )
    district_name = serializers.CharField(
        source="organization.district.short_name", read_only=True
    )
    organization_type_name = serializers.CharField(
        source="organization.organization_type.name", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "content",
            "author_name",
            "author_email",
            "organization",
            "organization_name",
            "district_name",
            "organization_type_name",
            "status",
            "status_display",
            "views_count",
            "suggestions_count",
            "comments_count",
            "is_approved",
            "created_at",
        ]
        read_only_fields = [
            "views_count",
            "suggestions_count",
            "is_approved",
            "created_at",
        ]


class QuestionDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для детального просмотра вопроса
    """

    author_name = serializers.CharField(max_length=255)
    author_email = serializers.EmailField(allow_blank=True, required=False)
    organization_detail = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    suggestions = SuggestionListSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    can_add_suggestion = serializers.BooleanField(read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "content",
            "author_name",
            "author_email",
            "organization",
            "organization_detail",
            "status",
            "status_display",
            "processed_by",
            "processed_at",
            "views_count",
            "suggestions_count",
            "suggestions",
            "comments",
            "can_add_suggestion",
            "is_approved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "views_count",
            "suggestions_count",
            "is_approved",
            "created_at",
            "updated_at",
        ]

    def get_organization_detail(self, obj):
        """Детальная информация об организации"""
        if obj.organization:
            return {
                "id": obj.organization.id,
                "short_name": obj.organization.short_name,
                "full_name": obj.organization.full_name,
                "district": (
                    obj.organization.district.short_name
                    if obj.organization.district
                    else None
                ),
                "type": (
                    obj.organization.organization_type.name
                    if obj.organization.organization_type
                    else None
                ),
                "coordinates": obj.organization.coordinates,
            }
        return None


class QuestionCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания вопроса
    """

    author_name = serializers.CharField(max_length=255)
    author_email = serializers.EmailField(allow_blank=True, required=False)

    class Meta:
        model = Question
        fields = [
            "organization",
            "author_name",
            "author_email",
            "title",
            "content",
        ]

    def validate_organization(self, value):
        """Проверяем, что организация существует и активна"""
        if value and value.status != "ACTIVE":
            raise serializers.ValidationError("Организация не активна")
        return value
