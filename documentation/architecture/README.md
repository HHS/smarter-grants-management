# Smarter Grants Management: Opportunity Architecture

Architecture documentation for Opportunity, the part of Smarter Grants Management in Nava scope. It is in development and not yet in production. It follows the [C4 model](https://c4model.com), starting with the whole system and zooming in to containers, deployment, components and key runtime flows.

## Start here

- **[Architecture document](architecture.md):** the full write-up with diagrams.

## Contents of the architecture document

1. [Reading the diagrams](architecture.md#1-reading-the-diagrams): what the shapes, colors and borders mean.
2. [Planned changes](architecture.md#2-planned-changes): decided changes and items under consideration.
3. [System context](architecture.md#3-system-context): users and the outside systems Opportunity depends on.
4. [Containers](architecture.md#4-containers): the separately running parts and their data stores.
5. [Deployment and network path](architecture.md#5-deployment-and-network-path): how traffic reaches the frontend and the API in AWS.
6. [API components](architecture.md#6-api-components): the API's domain and cross-cutting components, including [access control](architecture.md#access-control).
7. [Workflow Worker components](architecture.md#7-workflow-worker-components): how workflow events are processed.
8. [Key flows](architecture.md#8-key-flows): file upload and virus scan, and workflow events.
9. [Maintenance mode configuration](architecture.md#9-maintenance-mode-configuration): how maintenance-mode settings reach the API.

## Working on the docs

- **[CONTRIBUTING.md](CONTRIBUTING.md):** how to edit the model and regenerate the diagrams.
- **[update-diagrams.sh](update-diagrams.sh):** regenerates the diagrams from the model.
- **[architecture.dsl](architecture.dsl):** the Structurizr model that every diagram is generated from.
- **[diagrams/svg/](diagrams/svg/):** the generated diagrams.
