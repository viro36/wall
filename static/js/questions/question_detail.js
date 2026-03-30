

// Функция для показа/скрытия комментариев
function toggleComments(suggestionId) {
    const commentsDiv = document.getElementById(`comments-${suggestionId}`);
    if (commentsDiv) {
        if (commentsDiv.style.display === 'none' || !commentsDiv.style.display) {
            commentsDiv.style.display = 'block';
        } else {
            commentsDiv.style.display = 'none';
        }
    } else {
        console.error('Comments div not found for suggestion:', suggestionId);
    }
}

// Функция для загрузки комментариев
function loadComments(suggestionId) {
    const commentsList = document.querySelector(`#comments-${suggestionId} .comments-list`);
    if (commentsList && commentsList.children.length === 0) {
        // Здесь можно добавить HTMX запрос для загрузки комментариев
        htmx.ajax('GET', `/api/comments/?suggestion=${suggestionId}`, {
            target: `#comments-${suggestionId} .comments-list`
        });
    }
}

// Функция для показа формы ответа
function showReplyForm(commentId, authorName) {
    // Скрываем все остальные формы
    document.querySelectorAll('[id^="reply-form-"]').forEach(form => {
        form.style.display = 'none';
    });

    // Показываем нужную форму
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    if (replyForm) {
        replyForm.style.display = 'block';

        // Добавляем или обновляем индикатор ответа
        let replyIndicator = replyForm.querySelector('.reply-indicator');
        if (!replyIndicator) {
            replyIndicator = document.createElement('div');
            replyIndicator.className = 'reply-indicator mb-2 small text-primary';
            replyForm.insertBefore(replyIndicator, replyForm.firstChild);
        }
        replyIndicator.innerHTML = `<i class="fa-solid fa-reply me-1"></i>Ответ для <strong>${authorName}</strong>`;

        // Фокусируемся на поле имени
        const nameInput = replyForm.querySelector('input[name="author_name"]');
        if (nameInput) {
            nameInput.focus();
        }

        // Прокручиваем к форме
        replyForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
        console.error('Reply form not found for comment:', commentId);
    }
}

// Функция для скрытия формы ответа
function hideReplyForm(commentId) {
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    if (replyForm) {
        replyForm.style.display = 'none';
    }
}

// Функция для обновления счетчика комментариев
function updateCommentsCount(suggestionId) {
    const count = document.querySelectorAll(`#comments-${suggestionId} .comment`).length;
    const btn = document.querySelector(`button[onclick*="toggleComments(${suggestionId})"]`);
    if(btn) {
        btn.innerHTML = `<i class="fa-regular fa-comment me-1"></i>Комментарии <span class="comments-count-badge">${count}</span>`;
    }
}

// Обработчик после успешной отправки комментария
document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.requestConfig.path.includes('/comments/') && evt.detail.successful) {
        // Находим ID предложения из URL
        const match = evt.detail.requestConfig.path.match(/\/suggestions\/(\d+)\/comments\//);
        if (match && match[1]) {
            updateCommentsCount(match[1]);
        }
    }
});

// Подсветка кнопки после голосования
document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.requestConfig.path.includes('/vote/')) {
        const button = evt.detail.elt;
        const suggestionCard = button.closest('.suggestion-card');

        if (suggestionCard) {
            suggestionCard.querySelectorAll('.vote-btn').forEach(btn => {
                btn.classList.remove('liked', 'disliked');
            });

            const voteValue = evt.detail.requestConfig.vals?.vote;
            if (voteValue == 1) {
                button.classList.add('liked');
            } else if (voteValue == -1) {
                button.classList.add('disliked');
            }
        }
    }
});

// Обновление счетчика предложений
document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.id === 'suggestions-list') {
        const count = document.querySelectorAll('#suggestions-list .suggestion-card').length;
        const headerElement = document.querySelector('h3.h4.mb-0');
        if (headerElement) {
            headerElement.innerHTML = `<i class="fa-solid fa-lightbulb me-2 text-primary"></i>Предложения (${count})`;
        }
    }
});

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

// Функция для обработки после добавления комментария
function handleCommentResponse(element, suggestionId, commentId = null) {
    return function(evt) {
        if (evt.detail.successful) {
            const form = element;
            form.reset();

            if (commentId) {
                // Для ответов скрываем форму и показываем уведомление
                document.getElementById(`reply-form-${commentId}`).style.display = 'none';
                showNotification('Ответ добавлен', 'success');

                // Раскрываем комментарии, если они скрыты
                const parentComment = document.getElementById(`comment-${commentId}`);
                if (parentComment) {
                    const repliesContainer = parentComment.querySelector('.comment-replies');
                    if (repliesContainer) {
                        repliesContainer.style.display = 'block';
                    }
                }
            } else {
                // Для корневых комментариев
                showNotification('Комментарий добавлен', 'success');
            }

            // Обновляем счетчик комментариев
            setTimeout(() => {
                const count = document.querySelectorAll(`#comments-${suggestionId} .comment`).length;
                const btn = document.querySelector(`button[onclick*="toggleComments(${suggestionId})"]`);
                if (btn) {
                    btn.innerHTML = `<i class="fa-regular fa-comment me-1"></i>Комментарии <span class="comments-count-badge">${count}</span>`;
                }
            }, 100);
        }
    };
}
