# Grants Management API

## Introduction

This is the API that backs Grants Management's API as well
as backend scripts and services.

## Project Directory Structure

```text
root
├── src
│    └── db
│        └── models          DB model definitions
│        └── migrations      DB migration configs
│            └── versions    The DB migrations
│    └── adapters            Any external adapters for other services
│    └── api                 API route logic
|    └── services            Methods for service layer
│    └── constants           Constants used elsewhere in our implementation
│    └── static              Statically defined API files
│
└── tests
└── local.env           Environment variable configuration for local files
└── Makefile            Frequently used CLI commands for docker and utilities
└── pyproject.toml      Python project configuration file
└── Dockerfile          Docker build file for project
└── gunicorn.conf.py    Gunicorn service configuration
└── docker-compose.yml  Config file for docker compose tool, used for local development
```

## Local Development

See [development.md](../../documentation/api/development.md) for installation and development instructions.

## Running tests locally
1. Run `make init` or have run it previously
2. Run the tests `make test`

You can also run only certain tests by pattern matching the file name and log more while running the tests:
```bash
make test args="tests/api/healthcheck/test_healthcheck_routes.py"
make test args="tests/api"
```

## Technical Information

* [API Technical Overview](/documentation/api/technical-overview.md)
* [Database Management](/documentation/api/database/database-management.md)
* [Formatting and Linting](/documentation/api/formatting-and-linting.md)
* [Writing Tests](/documentation/api/writing-tests.md)
* [Logging configuration](/documentation/api/monitoring-and-observability/logging-configuration.md)
* [Logging conventions](/documentation/api/monitoring-and-observability/logging-conventions.md)
