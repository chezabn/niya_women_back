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
	python niya/manage.py makemigrations

# ==================================================================================== #
# MIGRATE
# ==================================================================================== #

## migrate: migrate
.PHONY: migrate
migrate:
	python niya/manage.py migrate

# ==================================================================================== #
# UPDATE DATABASE
# ==================================================================================== #

## db: update database with makemigrations and migrate
.PHONY: db
db: migrations migrate

# ==================================================================================== #
# RUN SERVER
# ==================================================================================== #

## run-server: launch server
.PHONY: run-server
run-server:
	python niya/manage.py runserver 0.0.0.0:5001

# ==================================================================================== #
# FREEZE
# ==================================================================================== #

## freeze: Add dependancies to requirements.txt
.PHONY: freeze
freeze:
	pip freeze > niya/requirements.txt

# ==================================================================================== #
# BUILD AUTH API SERVICE
# ==================================================================================== #

## build-auth-api: Build image of the auth-api service
.PHONY: build-auth-api
build-auth-api:
	docker build -f niya/Dockerfile -t auth_api .


# ==================================================================================== #
# STOP DATABASE SERVICE
# ==================================================================================== #

## stop-db: stop container of database
.PHONY: stop-db
stop-db:
	docker compose --env-file database/.env -f database/docker-compose.yml down

# ==================================================================================== #
# RUN DATABASE SERVICE
# ==================================================================================== #

## run-db: run container of database
.PHONY: run-db
run-db:stop-db build-auth-api
	docker compose --env-file database/.env -f database/docker-compose.yml up -d