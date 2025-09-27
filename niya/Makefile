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

## build-auth-api: Build image of the auth-api service
.PHONY: build-auth-api
build-auth-api:
	docker build -f niya/Dockerfile -t auth_api .

# ==================================================================================== #
# STOP ALL SERVICES
# ==================================================================================== #

## stop-dev: stop container of database
.PHONY: stop-dev
stop-dev:
	docker compose --env-file database/.env.dev -f database/docker-compose.yml down

# ==================================================================================== #
# RUN ALL SERVICES
# ==================================================================================== #

## run-dev: run container of database
.PHONY: run-dev
run-dev:stop-db build-auth-api
	docker compose --env-file database/.env.dev -f database/docker-compose.yml up -d
