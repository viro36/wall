import os
import uuid

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import F

from apps.organizations.models import District

from .forms import QuestionForm, SuggestionForm
from .models import Question


def home(request):
    """
    Главная страница со списком вопросов
    """
    questions_list = (
        Question.objects.filter(is_approved=True)
        .select_related("organization__district", "organization__organization_type")
        .prefetch_related("comments")
        .order_by("-created_at")
    )

    paginator = Paginator(questions_list, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request, "questions/home.html", {"questions": page_obj, "page_obj": page_obj}
    )


def ask_question(request):
    """
    Форма создания вопроса
    """
    if request.method == "POST":
        form = QuestionForm(
            request.POST, request.FILES
        )  # Добавлен request.FILES для загрузки файлов
        if form.is_valid():
            question = form.save()

            messages.success(
                request,
                "Ваш вопрос успешно создан!",
            )
            return redirect("question_detail", pk=question.id)
    else:
        form = QuestionForm()

    context = {
        "form": form,
        "ckeditor_enabled": True,
    }

    return render(request, "questions/ask_question.html", context)


def question_detail(request, pk):
    """
    Детальная страница вопроса
    """
    question = get_object_or_404(
        Question.objects.select_related(
            "organization__district", "organization__organization_type", "processed_by"
        ).prefetch_related("suggestions", "comments"),
        pk=pk,
    )

    # Проверяем, смотрел ли пользователь этот вопрос в текущей сессии
    session_key = f"viewed_question_{pk}"

    if not request.session.get(session_key):
        # Если не смотрел, увеличиваем счетчик и запоминаем в сессии
        Question.objects.filter(pk=pk).update(views_count=F("views_count") + 1)
        question.refresh_from_db()

        # Запоминаем, что пользователь уже видел этот вопрос
        request.session[session_key] = True

    # Создаем форму для предложения
    suggestion_form = SuggestionForm()

    # Получаем все районы для выпадающего списка
    districts = District.objects.all()

    return render(
        request,
        "questions/question_detail.html",
        {
            "question": question,
            "suggestion_form": suggestion_form,
            "districts": districts,
        },
    )


def edit_question(request, pk):
    """
    Редактирование вопроса (только для автора)
    """
    question = get_object_or_404(Question, pk=pk)

    # Проверяем, может ли пользователь редактировать
    # Можно добавить проверку по email или сессии

    if request.method == "POST":
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, "Вопрос успешно обновлен!")
            return redirect("question_detail", pk=question.id)
    else:
        form = QuestionForm(instance=question)

    return render(
        request, "questions/edit_question.html", {"form": form, "question": question}
    )


@csrf_exempt
def upload_ckeditor_image(request):
    """
    Эндпоинт для загрузки изображений в CKEditor
    """
    if request.method == "POST" and request.FILES.get("upload"):
        uploaded_file = request.FILES["upload"]

        # Проверяем тип файла
        ext = os.path.splitext(uploaded_file.name)[1].lower().replace(".", "")
        allowed_extensions = settings.CKEDITOR_5_UPLOAD_FILE_TYPES

        if ext not in allowed_extensions:
            return JsonResponse(
                {
                    "error": {
                        "message": f'Неподдерживаемый тип файла. Разрешены: {", ".join(allowed_extensions)}'
                    }
                },
                status=400,
            )

        # Генерируем уникальное имя файла
        filename = f"ckeditor/{uuid.uuid4()}.{ext}"

        # Сохраняем файл
        saved_path = default_storage.save(filename, uploaded_file)
        file_url = default_storage.url(saved_path)

        return JsonResponse({"url": file_url})

    return JsonResponse({"error": {"message": "Файл не найден"}}, status=400)
