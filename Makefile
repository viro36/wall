venv:
	python3 -m venv .venv

# source .venv/bin/activate

freeze:
	pip3 freeze > requirements.txt

req:
	pip3 install -r requirements.txt


# ----------------------------------------

# SELECT setval(pg_get_serial_sequence('users', 'id'), coalesce(max(id)+1, 1), false) FROM users;

# docker-compose exec wall python3 manage.py startapp

build-d:
	docker-compose -f docker-compose.yml up --build -d --remove-orphans

build-p:
	docker-compose -f docker-compose.prod.yml up --build -d --remove-orphans

build-timeout:
	COMPOSE_HTTP_TIMEOUT=400 docker-compose up --build -d --remove-orphans

build-no:
	docker-compose build --no-cache

up-d:
	docker-compose -f docker-compose.yml up -d

up-p:
	docker-compose -f docker-compose.prod.yml up -d

up-timeout:
	COMPOSE_HTTP_TIMEOUT=400 docker-compose up -d

down-d:
	docker-compose -f docker-compose.yml down

down-p:
	docker-compose -f docker-compose.prod.yml down

logs:
	docker-compose logs

shell-d:
	docker-compose exec wall python manage.py shell

dbshell:
	docker-compose exec wall python manage.py dbshell

migrate-d:
	docker-compose exec wall python manage.py migrate --noinput

makemigrations:
	docker-compose exec wall python manage.py makemigrations

flush:
	docker-compose exec wall python manage.py flush

reset_db:
	docker-compose exec wall python manage.py reset_db

showmigrations:
	docker-compose exec wall python manage.py showmigrations

superuser:
	docker-compose exec wall python manage.py createsuperuser

collectstatic:
	docker-compose exec wall python manage.py collectstatic --no-input --clear

findstatic:
	docker-compose exec wall python manage.py findstatic css/style.css --verbosity 2

sessioninfo:
	docker-compose exec wall python manage.py sessioninfo

pytest:
	docker-compose exec wall python -m pytest -v

pytest-orgs:
	docker-compose exec wall python -m pytest -v apps/organizations/tests/

pytest-q:
	docker-compose exec wall python -m pytest -v apps/questions/tests/

pytest-all:
	docker-compose exec wall python -m pytest apps/ -v --cov=apps --cov-report=term-missing

db-connect:
	docker-compose exec wall psql -h postgres-db -U admin -d wall

inspectdb:
	docker-compose exec wall python manage.py inspectdb > models.py

cache:
	docker-compose exec wall python manage.py createcachetable

show_urls:
	docker-compose exec wall python manage.py show_urls

dump-all-db:
	docker exec -t --user postgres wall_postgres-db_1 pg_dumpall -c -U postgres > dump.sql

bash:
	docker-compose exec wall bash

load_districts:
	docker-compose exec wall python manage.py load_districts

load_district-p:
	docker-compose -f docker-compose.prod.yml exec wall python manage.py load_districts

load_orgs:
	docker-compose exec wall python manage.py import_orgs apps/organizations/fixtures/orgs.csv

load_orgs-p:
	docker-compose -f docker-compose.prod.yml exec wall python manage.py import_orgs apps/organizations/fixtures/orgs.csv

# Обновить все организации, которые не обновлялись 30 дней
dadata_30:
	docker-compose exec wall python manage.py update_organizations_from_dadata --days 30

dadata_30-p:
	docker-compose -f docker-compose.prod.yml exec wall python manage.py update_organizations_from_dadata --days 30

# Обновить все организации
dadata_all:
	docker-compose exec wall python manage.py update_organizations_from_dadata --all

dadata_all-p:
	docker-compose -f docker-compose.prod.yml exec wall python manage.py update_organizations_from_dadata --all

# Обновить все организации с задержкой 0.5 сек (без лимита)
dadata_delay:
	docker-compose exec wall python manage.py update_organizations_from_dadata --all --delay 0.5

dadata_delay-p:
	docker-compose -f docker-compose.prod.yml exec wall python manage.py update_organizations_from_dadata --all --delay 0.5

# Обновить конкретную организацию
# python manage.py update_organizations_from_dadata --inn 3601234567

# ============================================
# ПРОДАКШЕН КОМАНДЫ
# ============================================

# Переменные
COMPOSE_FILE = docker-compose.prod.yml
BACKUP_DIR = ./backups

# Алиасы
down: down-p
up: up-p
build: build-p
logs: logs-p
shell: shell-p

# Создание директории для бэкапов
$(BACKUP_DIR):
	mkdir -p $(BACKUP_DIR)

# Бэкап базы данных
backup: $(BACKUP_DIR)
	@echo "=== Создание бэкапа БД ==="
	@POSTGRES_USER=$$(grep POSTGRES_USER .env.prod | cut -d '=' -f2 | tr -d '\r'); \
	POSTGRES_DBNAME=$$(grep POSTGRES_DBNAME .env.prod | cut -d '=' -f2 | tr -d '\r'); \
	POSTGRES_PASS=$$(grep POSTGRES_PASS .env.prod | cut -d '=' -f2 | tr -d '\r'); \
	POSTGRES_HOST=$$(grep POSTGRES_HOST .env.prod | cut -d '=' -f2 | tr -d '\r'); \
	docker-compose -f $(COMPOSE_FILE) exec -T postgres-db bash -c "PGPASSWORD=$$POSTGRES_PASS pg_dump -h localhost -U $$POSTGRES_USER $$POSTGRES_DBNAME" > $(BACKUP_DIR)/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Бэкап создан в $(BACKUP_DIR)"

# Восстановление из бэкапа
restore:
	@echo "=== Восстановление БД из бэкапа ==="
	@echo "ВНИМАНИЕ: Текущие данные будут УДАЛЕНЫ и заменены данными из бэкапа!"
	@read -p "Вы уверены? (y/N): " confirm; \
	if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
		echo "Восстановление отменено"; \
		exit 1; \
	fi
	@echo ""
	@echo "Доступные бэкапы:"
	@ls -1 $(BACKUP_DIR)/backup_*.sql 2>/dev/null || (echo "Нет бэкапов" && exit 1)
	@read -p "Введите имя файла бэкапа (например, backup_20241201_120000.sql): " filename; \
	if [ -f "$(BACKUP_DIR)/$$filename" ]; then \
		echo "Восстанавливаем $$filename..."; \
		POSTGRES_USER=$$(grep POSTGRES_USER .env.prod | cut -d '=' -f2 | tr -d '\r'); \
		POSTGRES_DBNAME=$$(grep POSTGRES_DBNAME .env.prod | cut -d '=' -f2 | tr -d '\r'); \
		POSTGRES_PASS=$$(grep POSTGRES_PASS .env.prod | cut -d '=' -f2 | tr -d '\r'); \
		echo "-> Очищаем базу данных..."; \
		docker-compose -f $(COMPOSE_FILE) exec -T postgres-db bash -c "PGPASSWORD=$$POSTGRES_PASS psql -h localhost -U $$POSTGRES_USER -d $$POSTGRES_DBNAME -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'" 2>/dev/null || true; \
		echo "-> Восстанавливаем данные..."; \
		docker-compose -f $(COMPOSE_FILE) exec -T postgres-db bash -c "PGPASSWORD=$$POSTGRES_PASS psql -h localhost -U $$POSTGRES_USER -d $$POSTGRES_DBNAME" < $(BACKUP_DIR)/$$filename; \
		echo "База данных восстановлена"; \
		echo "-> Применяем миграции..."; \
		docker-compose -f $(COMPOSE_FILE) exec wall python manage.py migrate --noinput; \
	else \
		echo "Файл $$filename не найден"; \
	fi

# Полная пересборка с сохранением данных
rebuild: backup down-p build-p up-p migrate-p
	@echo "=== Пересборка завершена ==="
	@echo "Данные сохранены"
	@echo "Контейнеры пересобраны"
	@echo "Миграции применены"

# Быстрая пересборка (без бэкапа, только код)
rebuild-fast: down-p build-p up-p migrate-p
	@echo "=== Быстрая пересборка завершена ==="

# Миграции для продакшена
migrate-p:
	docker-compose -f $(COMPOSE_FILE) exec wall python manage.py migrate --noinput

# Просмотр статуса
status:
	docker-compose -f $(COMPOSE_FILE) ps

# Логи только celery
logs-celery:
	docker-compose -f $(COMPOSE_FILE) logs celery_worker celery_beat -f

# Перезапустить только wall
restart-wall:
	docker-compose -f $(COMPOSE_FILE) restart wall

# Войти в продакшен контейнер
shell-p:
	docker-compose -f $(COMPOSE_FILE) exec wall /bin/bash

# Посмотреть логи продакшена
logs-p:
	docker-compose -f $(COMPOSE_FILE) logs -f

# Остановка продакшена
down-p:
	docker-compose -f $(COMPOSE_FILE) down

# Запуск продакшена
up-p:
	docker-compose -f $(COMPOSE_FILE) up -d

# Сборка продакшена
build-p:
	docker-compose -f $(COMPOSE_FILE) build
