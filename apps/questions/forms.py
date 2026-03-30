from django import forms
from .models import Question, Suggestion, Comment
from django_ckeditor_5.widgets import CKEditor5Widget

from apps.organizations.models import District, Organization, OrganizationType


class QuestionForm(forms.ModelForm):
    """
    Форма для создания вопроса с динамической подгрузкой организаций
    """

    # Поля для выбора (их нет в модели, они для AJAX)
    district = forms.ModelChoiceField(
        queryset=District.objects.all(),
        required=False,
        label="Район",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "hx-get": "/api/get-organization-types-html/",  # Используем HTML эндпоинт
                "hx-target": "#id_organization_type_container",
                "hx-trigger": "change",
                "hx-indicator": ".htmx-indicator",
                "hx-swap": "innerHTML",
            }
        ),
    )

    organization_type = forms.ModelChoiceField(
        queryset=OrganizationType.objects.none(),
        required=False,
        label="Тип организации",
        widget=forms.Select(attrs={"class": "form-select", "disabled": "disabled"}),
    )

    author_name = forms.CharField(
        max_length=255,
        label="Ваше имя или ник",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Как к вам обращаться?"}
        ),
    )

    author_email = forms.EmailField(
        required=False,
        label="Email (для уведомлений)",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "example@mail.ru (необязательно)",
            }
        ),
    )

    title = forms.CharField(
        max_length=500,
        label="Заголовок вопроса",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Кратко сформулируйте вопрос",
            }
        ),
    )

    content = forms.CharField(
        label="Текст вопроса",
        widget=CKEditor5Widget(
            attrs={"class": "django_ckeditor_5"}, config_name="extends"
        ),
    )

    organization = forms.ModelChoiceField(
        queryset=Organization.objects.filter(status="ACTIVE"),
        required=False,
        label="Организация",
        widget=forms.Select(attrs={"class": "form-select", "disabled": "disabled"}),
    )

    class Meta:
        model = Question
        fields = ["author_name", "author_email", "title", "content", "organization"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Настраиваем HTMX атрибуты для динамической загрузки
        self.fields["district"].widget.attrs["hx-indicator"] = "#district-indicator"

        # Делаем поля обязательными
        self.fields["author_name"].required = True
        self.fields["title"].required = True
        self.fields["content"].required = True


class SuggestionForm(forms.ModelForm):
    """
    Форма для создания предложения с динамической подгрузкой организаций
    """

    # Поля для выбора (их нет в модели, они для AJAX)
    district = forms.ModelChoiceField(
        queryset=District.objects.all(),
        required=False,
        label="Район",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "hx-get": "/api/get-organization-types-html/",
                "hx-target": "#id_suggestion_organization_type_container",
                "hx-trigger": "change",
                "hx-indicator": "#suggestion-district-indicator",
                "hx-swap": "innerHTML",
            }
        ),
    )

    organization_type = forms.ModelChoiceField(
        queryset=OrganizationType.objects.none(),
        required=False,
        label="Тип организации",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "disabled": "disabled",
                "id": "id_suggestion_organization_type",
            }
        ),
    )

    author_name = forms.CharField(
        max_length=255,
        label="Ваше имя или ник",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Как к вам обращаться?"}
        ),
    )

    content = forms.CharField(
        label="Текст предложения",
        widget=CKEditor5Widget(
            attrs={"class": "django_ckeditor_5"}, config_name="extends"
        ),
    )

    organization = forms.ModelChoiceField(
        queryset=Organization.objects.filter(status="ACTIVE"),
        required=False,
        label="Организация",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "disabled": "disabled",
                "id": "id_suggestion_organization",
            }
        ),
    )

    class Meta:
        model = Suggestion
        fields = ["author_name", "content", "organization"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Настраиваем HTMX атрибуты
        self.fields["district"].widget.attrs[
            "hx-indicator"
        ] = "#suggestion-district-indicator"

        # Делаем поля обязательными
        self.fields["author_name"].required = True
        self.fields["content"].required = True


class CommentForm(forms.ModelForm):
    """
    Форма для создания комментария (без email)
    """

    author_name = forms.CharField(
        max_length=255,
        label="Ваше имя",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Как к вам обращаться?",
                "required": "required",
            }
        ),
    )

    content = forms.CharField(
        label="Комментарий",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Напишите ваш комментарий...",
                "required": "required",
            }
        ),
    )

    class Meta:
        model = Comment
        fields = ["author_name", "content"]
