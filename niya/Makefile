# ==================================================================================== #
# VARIABLES
# ==================================================================================== #


# ==================================================================================== #
# HELPERS
# ==================================================================================== #
## help: print this help message
.PHONY: help
help:
	@echo 'Usage:'
	@sed -n 's/^##//p' ${MAKEFILE_LIST} | column -t -s ":" | sed -e 's/^/ /'

# ==================================================================================== #
# MIGRATIONS
# ==================================================================================== #

## migrations: make migrations
.PHONY: migrations
migrations:
	python manage.py makemigrations

## migrate: migrate
.PHONY: migrate
migrate:
	python manage.py migrate

## db: update database with makemigrations and migrate
.PHONY: db
db: migrations migrate

# ==================================================================================== #
# RUN SERVER
# ==================================================================================== #

## run-server: launch server
.PHONY: run-server
run-server:
	python manage.py runserver 0.0.0.0:5001

# ==================================================================================== #
# TEST
# ==================================================================================== #

## test: test auth app
.PHONY: test-auth
test-auth:
	python manage.py test authentication


## test: test company app
.PHONY: test-comp
test-comp:
	python manage.py test company

## test: test publication app
.PHONY: test-publ
test-publ:
	python manage.py test publication

## test: test all app in project
.PHONY: test
test:
	python manage.py test

# ==================================================================================== #
# FORMAT
# ==================================================================================== #

## black: do black for all project
.PHONY: black
black:
	black .


# ==================================================================================== #
# FREEZE
# ==================================================================================== #

## freeze: Add dependancies to requirements.txt
.PHONY: freeze
freeze:
	pip freeze > requirements.txt

# ==================================================================================== #
# BUILD AUTH API SERVICE
# ==================================================================================== #

## docker-build-api: Build image of the backend service
.PHONY: docker-build-api
docker-build-api:
	docker build -f ./docker/Dockerfile -t niyya_backend .

# ==================================================================================== #
# STOP ALL SERVICES
# ==================================================================================== #

## stop-db: stop sontainer of database
.PHONY: stop-db
stop-db:
	docker compose --env-file .env.dev -f ./docker/docker-compose.yml --project-name niyya-women down database

## stop-api: stop sontainer of api
.PHONY: stop-api
stop-api:
	docker compose --env-file .env.dev -f ./docker/docker-compose.yml --project-name niyya-women down backend

## stop-dev: stop container of niyya app
.PHONY: stop-dev
stop-dev:
	docker compose --env-file .env.dev -f ./docker/docker-compose.yml --project-name niyya-women down

# ==================================================================================== #
# RUN ALL SERVICES
# ==================================================================================== #

## run-dev: run container of database
.PHONY: run-db
run-db: stop-db
	docker compose --env-file .env.dev -f ./docker/docker-compose.yml --project-name niyya-women up -d database

## run-dev: run container of api
.PHONY: run-api
run-api: stop-api docker-build-api
	docker compose --env-file .env.dev -f ./docker/docker-compose.yml --project-name niyya-women up -d backend

## run-dev: run container of niyya app
.PHONY: run-dev
run-dev: stop-dev docker-build-api
	docker compose --env-file .env.dev -f ./docker/docker-compose.yml --project-name niyya-women up -d