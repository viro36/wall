function suggestionForm() {
    return {
        isSubmitting: false,
        ckEditorInstance: null,
        contentCounter: null,
        contentInput: null,

        init() {
            this.contentCounter = document.getElementById('suggestion-content-counter');
            this.contentInput = document.getElementById('id_content');

            if (this.contentCounter) {
                this.contentCounter.textContent = '0/5000';
            }

            // Сохраняем экземпляр глобально
            window.suggestionFormInstance = this;

            // Инициализируем CKEditor
            this.initCKEditor();

            // Инициализируем загрузку организаций для формы предложения
            this.initOrganizationLoader();

            // Добавляем обработчик для успешной отправки формы предложения
            this.initFormSubmitHandler();
        },

        initCKEditor() {
            const checkCKEditor = setInterval(() => {
                if (window.ClassicEditor && document.querySelector('#cke_id_content')) {
                    clearInterval(checkCKEditor);

                    ClassicEditor
                        .create(document.querySelector('#cke_id_content'), {
                            language: 'ru',
                            placeholder: 'Опишите ваше предложение подробнее...',
                            toolbar: {
                                items: [
                                    'heading', '|',
                                    'bold', 'italic', 'underline', 'strikethrough', '|',
                                    'bulletedList', 'numberedList', '|',
                                    'alignment', '|',
                                    'link', 'blockQuote', '|',
                                    'imageUpload',
                                    '|',
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
                            }
                        })
                        .then(editor => {
                            this.ckEditorInstance = editor;

                            editor.model.document.on('change:data', () => {
                                this.updateCKEditorCounter();
                            });

                            setTimeout(() => this.updateCKEditorCounter(), 500);

                            console.log('CKEditor initialized successfully');
                        })
                        .catch(error => {
                            console.error('CKEditor initialization error:', error);
                        });
                }
            }, 100);
        },

        initOrganizationLoader() {
            const districtSelect = document.getElementById('id_district');

            console.log('District select found, setting up handlers');

            // Обработчик после запроса HTMX
            document.addEventListener('htmx:afterRequest', (evt) => {
                console.log('HTMX afterRequest:', evt.detail.target?.id);

                // Для типов организаций
                if (evt.detail.target && evt.detail.target.id === 'id_organization_type_container') {
                    console.log('Processing organization types response');
                    const responseText = evt.detail.xhr.responseText;
                    const container = document.getElementById('id_organization_type_container');

                    // Создаем select с опциями и правильными атрибутами
                    let selectHtml = '<select name="organization_type" id="id_organization_type" class="form-select"';
                    selectHtml += ' hx-get="/api/get-organizations-html/"';
                    selectHtml += ' hx-target="#id_organization_container"';
                    selectHtml += ' hx-trigger="change"';
                    selectHtml += ' hx-indicator="#type-indicator"';
                    selectHtml += ' hx-swap="innerHTML"';
                    selectHtml += ' hx-include="#id_district"';
                    selectHtml += '>';
                    selectHtml += responseText;
                    selectHtml += '</select>';

                    container.innerHTML = selectHtml;

                    this.enableTypeSelect();
                }

                // Для организаций
                if (evt.detail.target && evt.detail.target.id === 'id_organization_container') {
                    console.log('Processing organizations response');
                    const responseText = evt.detail.xhr.responseText;
                    const container = document.getElementById('id_organization_container');

                    // Создаем select с опциями
                    let selectHtml = '<select name="organization_select" id="id_organization" class="form-select"';
                    selectHtml += ' onchange="document.getElementById(\'id_organization_selected\').value = this.value">';
                    selectHtml += responseText;
                    selectHtml += '</select>';

                    container.innerHTML = selectHtml;

                    this.enableOrganizationSelect();
                }
            });

            // Сброс при изменении района
            districtSelect.addEventListener('htmx:beforeRequest', () => {
                console.log('Before request, resetting fields');
                this.resetDependentFields();
            });
        },

        enableTypeSelect() {
            const typeSelect = document.getElementById('id_organization_type');
            if (typeSelect) {
                typeSelect.disabled = false;

                // Добавляем атрибуты для HTMX (на всякий случай, если их нет)
                typeSelect.setAttribute('hx-get', '/api/get-organizations-html/');
                typeSelect.setAttribute('hx-target', '#id_organization_container');
                typeSelect.setAttribute('hx-trigger', 'change');
                typeSelect.setAttribute('hx-indicator', '#type-indicator');
                typeSelect.setAttribute('hx-swap', 'innerHTML');
                typeSelect.setAttribute('hx-include', '#id_district');

                if (typeof htmx !== 'undefined') {
                    htmx.process(typeSelect);
                }
            }
        },

        enableOrganizationSelect() {
            const orgSelect = document.getElementById('id_organization');
            if (orgSelect) {
                orgSelect.disabled = false;

                // Добавляем обработчик для сохранения выбранной организации в скрытое поле
                orgSelect.addEventListener('change', function() {
                    document.getElementById('id_organization_selected').value = this.value;
                });
            }
        },

        resetDependentFields() {
            // Сбрасываем тип организации
            const typeContainer = document.getElementById('id_organization_type_container');
            if (typeContainer) {
                typeContainer.innerHTML = '<select name="organization_type" id="id_organization_type" class="form-select" disabled><option value="">---------</option></select>';
            }

            // Сбрасываем организацию
            const orgContainer = document.getElementById('id_organization_container');
            if (orgContainer) {
                orgContainer.innerHTML = '<select name="organization_select" id="id_organization" class="form-select" disabled><option value="">---------</option></select>';
            }

            // Очищаем скрытое поле
            document.getElementById('id_organization_selected').value = '';
        },

        initFormSubmitHandler() {
            // Обработчик только для успешной отправки формы предложения
            document.body.addEventListener('htmx:afterRequest', (evt) => {
                // Проверяем, что это POST запрос на добавление предложения
                if (evt.detail.requestConfig.method === 'POST' &&
                    evt.detail.requestConfig.path.includes('/api/questions/') &&
                    evt.detail.requestConfig.path.includes('/suggestions/')) {

                    console.log('Suggestion form response:', evt.detail);

                    if (evt.detail.successful) {
                        // Очищаем форму
                        const form = document.querySelector('#suggestion-form-container form');
                        if (form) {
                            form.reset();
                        }

                        // Очищаем CKEditor
                        if (this.ckEditorInstance) {
                            this.ckEditorInstance.setData('');
                        }

                        // Сбрасываем поля выбора организации
                        this.resetDependentFields();

                        // Обновляем счетчик предложений
                        const count = document.querySelectorAll('#suggestions-list .suggestion-card').length;
                        const headerElement = document.querySelector('h3.h4.mb-0');
                        if (headerElement) {
                            headerElement.innerHTML = '<i class="fa-solid fa-lightbulb me-2 text-primary"></i>Предложения (' + count + ')';
                        }

                        // Закрываем форму
                        setTimeout(() => {
                            const collapseElement = document.getElementById('addSuggestionForm');
                            if (collapseElement) {
                                // Убираем класс 'show' в любом случае
                                collapseElement.classList.remove('show');

                                // Пробуем использовать Bootstrap collapse
                                if (typeof bootstrap !== 'undefined') {
                                    try {
                                        const bsCollapse = bootstrap.Collapse.getInstance(collapseElement);
                                        if (bsCollapse) {
                                            bsCollapse.hide();
                                        } else {
                                            // Создаем новый экземпляр и сразу скрываем
                                            new bootstrap.Collapse(collapseElement, {
                                                toggle: false
                                            }).hide();
                                        }
                                    } catch (e) {
                                        console.warn('Bootstrap collapse error:', e);
                                        // Если Bootstrap не работает, просто скрываем через CSS
                                        collapseElement.style.display = 'none';
                                    }
                                } else {
                                    // Если Bootstrap не загружен, просто скрываем через CSS
                                    collapseElement.style.display = 'none';
                                }
                            }
                        }, 200); // Небольшая задержка для гарантии

                        // Показываем уведомление
                        showNotification('Предложение успешно добавлено!', 'success');
                    }
                }
            });
        },

        updateCKEditorCounter() {
            if (this.ckEditorInstance && this.contentCounter) {
                const text = this.ckEditorInstance.getData()
                    .replace(/<[^>]*>/g, '')
                    .replace(/&nbsp;/g, ' ')
                    .trim();

                const length = text.length;
                const maxLength = 5000;
                this.contentCounter.textContent = `${length}/${maxLength}`;

                this.contentCounter.classList.remove('warning', 'danger');

                if (length > 4900) {
                    this.contentCounter.classList.add('danger');
                } else if (length > 4500) {
                    this.contentCounter.classList.add('warning');
                }

                if (this.contentInput) {
                    this.contentInput.value = this.ckEditorInstance.getData();
                }
            }
        },

        closeForm() {
            const form = document.getElementById('addSuggestionForm');
            if (form) {
                const collapse = bootstrap.Collapse.getInstance(form);
                if (collapse) {
                    collapse.hide();
                }
            }
        }
    }
}

// Делаем функцию глобально доступной
window.suggestionForm = suggestionForm;

// Функция для показа уведомлений
function showNotification(message, type = 'success') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alert.style.zIndex = '9999';
    alert.style.maxWidth = '400px';
    alert.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fa-solid fa-${type === 'success' ? 'check-circle' : 'info-circle'} me-2 fa-lg"></i>
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close ms-3" data-bs-dismiss="alert"></button>
        </div>
    `;
    document.body.appendChild(alert);

    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}

// Обновляем счетчик предложений после добавления
document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.id === 'suggestions-list') {
        // Обновляем счетчик предложений в заголовке
        const suggestionList = document.querySelector('#suggestions-list');
        if (suggestionList) {
            const suggestionCount = suggestionList.children.length;
            const countElement = document.querySelector('h3.h4.mb-0');
            if (countElement) {
                countElement.innerHTML = `<i class="fa-solid fa-lightbulb me-2 text-primary"></i>Предложения (${suggestionCount})`;
            }
        }
    }
});

// Обработка ошибок
document.body.addEventListener('htmx:responseError', function(evt) {
    const errorDetail = evt.detail.xhr.responseJSON?.error || 'Произошла ошибка при отправке';
    showNotification(errorDetail, 'danger');
});


document.body.addEventListener('htmx:beforeSwap', function(evt) {
    if (evt.detail.target && evt.detail.target.id === 'suggestions-list') {
        // Проверяем, существует ли еще элемент в DOM
        if (!document.getElementById('suggestions-list')) {
            evt.detail.shouldSwap = false;
            return;
        }
        evt.detail.shouldSwap = true;
    }
});
