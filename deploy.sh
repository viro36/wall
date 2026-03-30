#!/bin/bash

# Проверка наличия .env.prod
if [ ! -f .env.prod ]; then
    echo "Создайте файл .env.prod из .env.prod.example"
    exit 1
fi

# Обновляем код
git pull

# Останавливаем старые контейнеры
docker-compose -f docker-compose.prod.yml down

# Собираем и запускаем новые
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Применяем миграции
docker-compose -f docker-compose.prod.yml exec wall python manage.py migrate --noinput

# Собираем статику
docker-compose -f docker-compose.prod.yml exec wall python manage.py collectstatic --noinput

# Проверяем статус
docker-compose -f docker-compose.prod.yml ps

echo "Деплой завершен!"
