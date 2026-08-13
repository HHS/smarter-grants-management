.PHONY : \
	release-build \
	build-dev \
	build-prod \
	dev \
	run-prod \
	stop \
	reinstall-deps

# Docker user configuration
# This logic avoids permission issues when mounting local volumes, which should
# be owned by the same UID for Linux distros. macOS can use root, but running
# with least privilege is better practice where possible.
#
# Can be set by adding user=<username> and/or uid=<id> after the make command.
# If not set explicitly, values are looked up from the current environment,
# otherwise fixed defaults are used. uid= defaults to 0 when user= is set (which
# makes sense for user=root; otherwise you probably want to set uid as well).
ifeq ($(user),)
RUN_USER ?= $(or $(strip $(USER)),nodummy)
RUN_UID ?= $(or $(strip $(shell id -u)),4000)
else
RUN_USER = $(user)
RUN_UID = $(or $(strip $(uid)),0)
endif

export RUN_USER
export RUN_UID

##################################################
# Release
##################################################

# Called by the root Makefile's release-build target, which passes the image
# tags via OPTS. --platform=linux/amd64 because ECS Fargate runs amd64 and this
# is frequently built on arm64 Macs.
release-build:
	docker buildx build \
		--target release \
		--platform=linux/amd64 \
		--build-arg RUN_USER=$(RUN_USER) \
		--build-arg RUN_UID=$(RUN_UID) \
		$(OPTS) \
		.

##################################################
# Local development
##################################################
build-dev: # Build the Next.js local dev server in Docker
	docker compose build --no-cache nextjs

build-prod: # Build the Next.js local prod server in Docker
	docker compose build --no-cache --progress plain nextjs-prod

reinstall-deps:
	rm -rf node_modules
	npm install

dev: # Run the Next.js local dev server in Docker
	docker compose up --detach nextjs
	docker compose logs --follow nextjs

run-prod: # Run the Next.js local prod server in Docker
	docker compose up --detach nextjs-prod
	docker compose logs --follow nextjs-prod

stop:
	docker compose down
