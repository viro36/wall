venv:
	python3 -m venv .venv

# source .venv/bin/activate

freeze:
	pip3 freeze > requirements.txt

req:
	pip3 install -r requirements.txt


# ----------------------------------------

# SELECT setval(pg_get_serial_sequence('users', 'id'), coalesce(max(id)+1, 1), false) FROM users;

# docker-compose exec witwall python3 manage.py startapp

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
	docker-compose exec witwall python manage.py shell

dbshell:
	docker-compose exec witwall python manage.py dbshell

migrate-d:
	docker-compose exec witwall python manage.py migrate --noinput

makemigrations:
	docker-compose exec witwall python manage.py makemigrations

flush:
	docker-compose exec witwall python manage.py flush

reset_db:
	docker-compose exec witwall python manage.py reset_db

showmigrations:
	docker-compose exec witwall python manage.py showmigrations

superuser:
	docker-compose exec witwall python manage.py createsuperuser

collectstatic:
	docker-compose exec witwall python manage.py collectstatic --no-input --clear

findstatic:
	docker-compose exec witwall python manage.py findstatic css/style.css --verbosity 2

sessioninfo:
	docker-compose exec witwall python manage.py sessioninfo

pytest:
	docker-compose exec witwall python -m pytest -v

pytest-orgs:
	docker-compose exec witwall python -m pytest -v apps/organizations/tests/

pytest-q:
	docker-compose exec witwall python -m pytest -v apps/questions/tests/

pytest-all:
	docker-compose exec witwall python -m pytest apps/ -v --cov=apps --cov-report=term-missing

db-connect:
	docker-compose exec witwall psql -h postgres-db -U admin -d witwall

inspectdb:
	docker-compose exec witwall python manage.py inspectdb > models.py

cache:
	docker-compose exec witwall python manage.py createcachetable

show_urls:
	docker-compose exec witwall python manage.py show_urls

dump-all-db:
	docker exec -t --user postgres witwall_postgres-db_1 pg_dumpall -c -U postgres > dump.sql

bash:
	docker-compose exec witwall bash

load_districts:
	docker-compose exec witwall python manage.py load_districts

load_orgs:
	docker-compose exec witwall python manage.py import_orgs apps/organizations/fixtures/orgs.csv

# Обновить все организации, которые не обновлялись 30 дней
dadata_30:
	docker-compose exec witwall python manage.py update_organizations_from_dadata --days 30

# Обновить все организации
dadata_all:
	docker-compose exec witwall python manage.py update_organizations_from_dadata --all

# Обновить все организации с задержкой 0.5 сек (без лимита)
dadata_delay:
	docker-compose exec witwall python manage.py update_organizations_from_dadata --all --delay 0.5

# Обновить конкретную организацию
# python manage.py update_organizations_from_dadata --inn 3601234567
