/**
 * Модуль для формы создания вопроса с CKEditor 5
 */
const QuestionForm = (function() {
    // Приватные переменные
    let titleInput = null;
    let contentInput = null;  // Будет скрытым полем для CKEditor
    let titleCounter = null;
    let contentCounter = null;
    let form = null;
    let ckEditorInstance = null;

    // Настройки
    const config = {
        titleMaxLength: 500,
        contentMaxLength: 5000,
        titleWarningThreshold: 450,
        titleDangerThreshold: 490,
        contentWarningThreshold: 4500,
        contentDangerThreshold: 4900
    };

    /**
     * Инициализация модуля
     */
    function init() {
        // Получаем элементы DOM
        titleInput = document.getElementById('id_title');
        contentInput = document.getElementById('id_content');  // Скрытое поле для CKEditor
        titleCounter = document.getElementById('title-counter');
        contentCounter = document.getElementById('content-counter');
        form = document.querySelector('form');

        // Инициализируем компоненты
        initCounters();
        initFormValidation();
        initResetButton();
        initCKEditor();
    }

    /**
     * Инициализация счетчиков символов
     */
    function initCounters() {
        if (titleInput && titleCounter) {
            // Устанавливаем maxlength
            titleInput.setAttribute('maxlength', config.titleMaxLength);

            // Обновляем счетчик при загрузке
            updateCounter(
                titleInput,
                titleCounter,
                config.titleMaxLength,
                config.titleWarningThreshold,
                config.titleDangerThreshold
            );

            // Добавляем обработчик события
            titleInput.addEventListener('input', function() {
                updateCounter(
                    this,
                    titleCounter,
                    config.titleMaxLength,
                    config.titleWarningThreshold,
                    config.titleDangerThreshold
                );
            });
        }

        if (contentCounter) {
            contentCounter.textContent = `0/${config.contentMaxLength}`;
        }
    }

    /**
     * Обновление счетчика символов
     */
    function updateCounter(input, counter, maxLength, warningThreshold, dangerThreshold) {
        const length = input.value.length;
        counter.textContent = `${length}/${maxLength}`;

        // Убираем все классы
        counter.classList.remove('warning', 'danger');

        // Добавляем соответствующий класс
        if (length > dangerThreshold) {
            counter.classList.add('danger');
        } else if (length > warningThreshold) {
            counter.classList.add('warning');
        }
    }

    /**
     * Обновление счетчика для CKEditor
     */
    function updateCKEditorCounter() {
        if (ckEditorInstance && contentCounter) {
            // Получаем текст без HTML
            const text = ckEditorInstance.getData()
                .replace(/<[^>]*>/g, '')  // Удаляем HTML теги
                .replace(/&nbsp;/g, ' ')   // Заменяем &nbsp; на пробелы
                .trim();

            const length = text.length;
            contentCounter.textContent = `${length}/${config.contentMaxLength}`;

            contentCounter.classList.remove('warning', 'danger');

            if (length > config.contentDangerThreshold) {
                contentCounter.classList.add('danger');
            } else if (length > config.contentWarningThreshold) {
                contentCounter.classList.add('warning');
            }

            // Обновляем скрытое поле
            if (contentInput) {
                contentInput.value = ckEditorInstance.getData();
            }
        }
    }

    /**
     * Инициализация CKEditor 5
     */
    function initCKEditor() {
        // Ждем загрузки CKEditor
        const checkCKEditor = setInterval(function() {
            if (window.ClassicEditor && document.querySelector('#cke_id_content')) {
                clearInterval(checkCKEditor);

                ClassicEditor
                    .create(document.querySelector('#cke_id_content'), {
                        language: 'ru',
                        placeholder: 'Опишите ваш вопрос подробнее...',
                        toolbar: {
                            items: [
                                'heading', '|',
                                'bold', 'italic', 'underline', 'strikethrough', '|',
                                'bulletedList', 'numberedList', '|',
                                'alignment', '|',
                                'link', 'blockQuote', '|',
                                'undo', 'redo'
                            ]
                        },
                        heading: {
                            options: [
                                { model: 'paragraph', title: 'Параграф', class: 'ck-heading_paragraph' },
                                { model: 'heading1', view: 'h1', title: 'Заголовок 1', class: 'ck-heading_heading1' },
                                { model: 'heading2', view: 'h2', title: 'Заголовок 2', class: 'ck-heading_heading2' },
                                { model: 'heading3', view: 'h3', title: 'Заголовок 3', class: 'ck-heading_heading3' }
                            ]
                        },
                        image: {
                            toolbar: ['imageTextAlternative', '|', 'imageStyle:alignLeft', 'imageStyle:alignCenter', 'imageStyle:alignRight']
                        },
                        table: {
                            contentToolbar: ['tableColumn', 'tableRow', 'mergeTableCells']
                        }
                    })
                    .then(editor => {
                        ckEditorInstance = editor;

                        // Обновляем счетчик при изменении содержимого
                        editor.model.document.on('change:data', () => {
                            updateCKEditorCounter();
                        });

                        // Обновляем счетчик при загрузке
                        setTimeout(updateCKEditorCounter, 500);
                    })
                    .catch(error => {
                        console.error('CKEditor initialization error:', error);
                    });
            }
        }, 100);
    }

    /**
     * Инициализация валидации формы
     */
    function initFormValidation() {
        if (!form) return;

        form.addEventListener('submit', function(event) {
            let isValid = true;

            // Валидация заголовка
            if (titleInput && titleInput.value.trim().length < 10) {
                showError(titleInput, 'Заголовок должен быть не короче 10 символов');
                isValid = false;
            } else if (titleInput) {
                clearError(titleInput);
            }

            // Валидация текста вопроса через CKEditor
            if (ckEditorInstance) {
                const text = ckEditorInstance.getData()
                    .replace(/<[^>]*>/g, '')
                    .replace(/&nbsp;/g, ' ')
                    .trim();

                if (text.length < 20) {
                    showCKEditorError('Текст вопроса должен быть не короче 20 символов');
                    isValid = false;
                } else {
                    clearCKEditorError();

                    // Обновляем скрытое поле перед отправкой
                    if (contentInput) {
                        contentInput.value = ckEditorInstance.getData();
                    }
                }
            }

            if (!isValid) {
                event.preventDefault();
                scrollToFirstError();
            }
        });

        // Очищаем ошибки заголовка при вводе
        if (titleInput) {
            titleInput.addEventListener('input', function() {
                clearError(this);
            });
        }
    }

    /**
     * Показать ошибку для обычного поля
     */
    function showError(input, message) {
        input.classList.add('is-invalid');

        let feedback = input.nextElementSibling;
        if (!feedback || !feedback.classList.contains('invalid-feedback')) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            input.parentNode.insertBefore(feedback, input.nextSibling);
        }
        feedback.textContent = message;
    }

    /**
     * Показать ошибку для CKEditor
     */
    function showCKEditorError(message) {
        const ckeContainer = document.querySelector('#cke_id_content').closest('.mb-3');
        if (ckeContainer) {
            let feedback = ckeContainer.querySelector('.invalid-feedback');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                ckeContainer.appendChild(feedback);
            }
            feedback.textContent = message;
            document.querySelector('#cke_id_content').classList.add('is-invalid');
        }
    }

    /**
     * Очистить ошибку для обычного поля
     */
    function clearError(input) {
        input.classList.remove('is-invalid');
        const feedback = input.nextElementSibling;
        if (feedback && feedback.classList.contains('invalid-feedback')) {
            feedback.remove();
        }
    }

    /**
     * Очистить ошибку для CKEditor
     */
    function clearCKEditorError() {
        document.querySelector('#cke_id_content').classList.remove('is-invalid');
        const ckeContainer = document.querySelector('#cke_id_content').closest('.mb-3');
        const feedback = ckeContainer.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }

    /**
     * Прокрутка к первому полю с ошибкой
     */
    function scrollToFirstError() {
        const firstError = document.querySelector('.is-invalid');
        if (firstError) {
            firstError.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        } else {
            // Если нет поля с классом is-invalid, ищем ошибку CKEditor
            const ckeError = document.querySelector('#cke_id_content');
            if (ckeError) {
                ckeError.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
        }
    }

    /**
     * Инициализация кнопки очистки
     */
    function initResetButton() {
        const resetBtn = document.querySelector('button[type="reset"]');
        if (resetBtn) {
            resetBtn.addEventListener('click', function(e) {
                if (!confirm('Вы уверены, что хотите очистить все поля?')) {
                    e.preventDefault();
                } else {
                    // Очищаем CKEditor если нужно
                    if (ckEditorInstance) {
                        ckEditorInstance.setData('');
                    }
                    if (titleInput) {
                        titleInput.value = '';
                        updateCounter(titleInput, titleCounter, config.titleMaxLength,
                                    config.titleWarningThreshold, config.titleDangerThreshold);
                    }
                    if (contentCounter) {
                        contentCounter.textContent = `0/${config.contentMaxLength}`;
                    }
                }
            });
        }
    }

    // Публичный API
    return {
        init: init,
        getCKEditorInstance: function() { return ckEditorInstance; },
        getConfig: function() { return config; }
    };
})();

// Инициализация после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    QuestionForm.init();
});
