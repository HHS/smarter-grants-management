/*
 * Smarter Grants Management: Opportunity. C4 architecture model (Structurizr DSL)
 *
 * Views
 *   Context       - the system, its users and external systems
 *   Containers    - deployable/runnable units and data stores
 *   ApiComponents - inside the API container, by domain
 *   ApiComponentsClean - same, without the routing edges
 *   Deployment    - AWS network entry path
 *   MaintenanceConfig - how maintenance-mode settings reach the API
 *   WorkerComponents - inside the workflow worker container
 *   FileUpload    - dynamic: upload, virus scan, result
 *   WorkflowEvent - dynamic: event publish and processing
 *
 * Render to SVG: see CONTRIBUTING.md
 * (run from documentation/architecture/).
 *
 * Modeling notes
 *   - Components are domain slices (routes + service + models), not layers.
 *     Source paths are listed in each component's technology field.
 *   - "Not Wired" = defined in code but not registered or deployed.
 *   - "Planned Removal" = built, but being removed, replaced or under review (API Gateway, Login.gov, SAM.gov).
 *   - "Subject to Change" = likely rewritten or dropped once the SSO integration is designed.
 *   - "Planned" = decided but not built yet (GrantSolutions SSO).
 */
workspace "Smarter Grants Management: Opportunity" "C4 model of Opportunity, the part of Smarter Grants Management in Nava scope" {

    !identifiers flat

    model {

        # ---------- People ----------
        grantor    = person "Grantor Staff" "Agency staff who manage announcements, application packages and workflows."
        automation = person "API Key Client" "Scripts or integrations that call the API directly with a user API key. None exist yet; E2E tests go through the frontend." "Automation"

        # ---------- External systems ----------
        loginGov   = softwareSystem "Login.gov"          "Identity provider the sign-in flow was first built for. GrantSolutions SSO will replace the Login.gov flow." "External,Planned Removal"
        grantSolutionsSso = softwareSystem "GrantSolutions SSO" "Identity provider grantors will sign in with. Replaces the Login.gov flow." "External,Planned"
        extAuthz   = softwareSystem "External Authorization Service (proposed)" "Part of Smarter Grants Management, being built outside Nava scope. Will decide what each user is authorized to access. Name and interface TBD." "External,Planned"
        cdr        = softwareSystem "Common Data Repository (CDR)" "Shared data store for Smarter Grants Management, being built outside Nava scope." "External,Planned"
        samGov     = softwareSystem "SAM.gov"            "Candidate source of Assistance Listing (CFDA) data. Source is TBD; may come from CDR instead." "External,Planned Removal"
        newRelic   = softwareSystem "New Relic"          "Proposed for APM, logs and alerting. Not set up yet." "External,Planned"

        gm = softwareSystem "Smarter Grants Management: Opportunity" "Lets grantor agencies create and manage funding announcements. In Nava scope." {

            # ---------- Containers ----------
            frontend = container "Web Frontend" "Grantor-facing web UI." "Next.js" "Web"

            apiGateway = container "API Gateway" "Front door for all API traffic, including the frontend (which has its own key with no rate limit). Rate-limits API key clients. Planned for removal." "AWS API Gateway" "Infrastructure,Planned Removal"

            api = container "API" "REST API for all grantor-facing operations." "Python (APIFlask, SQLAlchemy, boto3), Gunicorn on ECS Fargate" {

                group "Cross-cutting" {
                    pipeline        = component "Request Pipeline"       "App factory, CORS, structured logging with PII masking, schema validation and error envelope." "app.py, logs/, api/schemas, api/response.py"
                    maintenanceGate = component "Maintenance Mode Gate"  "Returns 503 + Retry-After for non-allowlisted paths when enabled." "api/maintenance_mode.py" "Not Wired"
                    authn           = component "Authentication"         "Runs before every domain component. Accepts a session token (X-MGMT-Token) or an API key (X-API-Key), and checks session tokens against their session record." "auth/multi_auth.py, auth/*_auth.py, api/internal"
                    authz           = component "Authorization Enforcer" "Relationship-based access checks: roles held on specific resources, inherited along the organization hierarchy. Called by domain services after loading the resource, so not middleware. Expected to delegate decisions to an external authorization service." "auth/authorization_enforcer.py" "Subject to Change"
                    dbAccess        = component "Database Access"        "Scoped SQLAlchemy session per request, lookup tables, pagination and full-text search helpers, resource-row automation." "adapters/db, db/models, pagination/, search/, db/resource_automation"
                }

                group "Domain" {
                    announcements  = component "Announcements"        "Announcements, attachments, application packages, instructions and audit history." "api/ + services/announcements"
                    assistance     = component "Assistance Listings"  "Search over imported Assistance Listings." "api/ + services/assistance_listings"
                    forms          = component "Form Catalog"         "Static catalog of supported Grants.gov forms." "api/forms, services/forms" "Static"
                    files          = component "File Uploads"         "Presigned uploads, scan-status callbacks and streamed scan results." "api/files_v1, services/files"
                    organizations  = component "Organizations"        "Grantor organization hierarchy and partner records. Likely to change with the SSO integration." "api/ + services/grantor_organizations, partners" "Subject to Change"
                    resources      = component "Resources & Roles"    "Users and roles assigned to typed resources. Likely to change with the SSO integration." "api/ + services/resources" "Subject to Change"
                    users          = component "Users & Sessions"     "Sign-in callback that creates a session and issues the API's session token, logout, current user, access checks, API key issuance. Likely to change with the SSO integration." "api/ + services/users, auth/api_key_handler.py" "Subject to Change"
                    workflowApi    = component "Workflows"            "Reads workflow state and audits; accepts workflow events." "api/ + services/workflows"
                    healthcheck    = component "Healthcheck"          "Liveness and database connectivity." "api/healthcheck"
                }
            }

            worker = container "Workflow Worker" "Consumes workflow events and advances state machines." "Python (SQLAlchemy, boto3) on ECS Fargate: flask workflow workflow-main" {
                workflowManager = component "Workflow Manager"   "Long-running SQS poll loop; parses events and hands them to handlers." "workflow/manager, task/sqs_processor.py, workflow/handler"
                stateMachines   = component "State Machines"     "Registered state machines and approval processing." "workflow/state_machine, registry, processor, service"
                statePersistence = component "State Persistence" "State machine extension that saves each workflow's current state." "workflow/state_persistence"
                listeners       = component "Workflow Listeners" "Side effects on transitions: audit history and email notifications." "workflow/listener"
            }

            taskRunner = container "Task Runner" "Scaffolding for short-lived ECS tasks run on a schedule, such as ETL jobs. No tasks deployed yet." "Python (SQLAlchemy) on ECS: flask task ..." "Batch,Scaffolding"

            scanner = container "File Scanner" "Virus-scans uploads with ClamAV and reports results to the API." "AWS Lambda (Python, boto3), ClamAV" "Lambda"

            database      = container "Database"         "Announcements, orgs, users, sessions, roles, workflows, listings." "PostgreSQL (RDS Aurora)" "Database"
            fileBucket    = container "File Storage"     "Uploaded files, split into unscanned/, scanned/ and infected/." "Amazon S3" "Database"
            scanCache     = container "File Scan Cache"  "Scan status per pending file, polled by the upload client." "Amazon DynamoDB" "Database"
            ses           = container "Email Service"    "Sends email notifications." "Amazon SES"
            workflowQueue = container "Workflow Queue"   "Workflow events waiting to be processed." "Amazon SQS" "Queue"
        }

        # ---------- People -> system ----------
        grantor    -> frontend   "Manages announcements using" "HTTPS via CloudFront"
        grantor    -> loginGov   "Sign-in flow built for (being replaced)"
        grantor    -> grantSolutionsSso "Will sign in with" "" "Planned"
        automation -> apiGateway "Calls" "HTTPS, X-API-Key"
        apiGateway -> pipeline   "Forwards requests to" "HTTPS via backend ALB"

        # All API traffic, including the frontend's, goes through API Gateway.
        frontend -> apiGateway "Makes API calls through" "JSON/HTTPS, X-MGMT-Token"
        frontend -> fileBucket "Uploads files to" "HTTPS, presigned URL"

        # ---------- API: cross-cutting ----------
        pipeline -> authn           "Passes every request to"
        pipeline -> maintenanceGate "Would gate requests through" "" "Not Wired"
        pipeline -> newRelic        "Could send APM data and logs to" "New Relic agent" "Planned"
        authn    -> dbAccess        "Looks up sessions, users and API keys via"
        authz    -> dbAccess        "Reads role assignments and resource relationships via"
        authz    -> extAuthz        "Checks and records access in" "" "Planned"
        dbAccess -> database        "Reads from and writes to" "SQL"

        # ---------- API: routing ----------
        authn -> announcements "Routes authenticated requests to" "" "Routing"
        authn -> assistance    "Routes authenticated requests to" "" "Routing"
        authn -> forms         "Routes authenticated requests to" "" "Routing"
        authn -> files         "Routes authenticated requests to" "" "Routing"
        authn -> organizations "Routes authenticated requests to" "" "Routing"
        authn -> resources     "Routes authenticated requests to" "" "Routing"
        authn -> users         "Routes authenticated requests to" "" "Routing"
        authn -> workflowApi   "Routes authenticated requests to" "" "Routing"
        pipeline -> healthcheck   "Routes unauthenticated health checks to" "" "Routing"

        # ---------- API: domain dependencies ----------
        announcements -> authz      "Checks privileges with"
        announcements -> dbAccess   "Persists announcements via"
        announcements -> fileBucket "Stores attachments in" "S3 API"

        assistance -> dbAccess "Searches listings via"

        files -> fileBucket "Issues presigned upload URLs for" "S3 API"
        files -> scanCache  "Creates and polls scan records in" "DynamoDB API"
        files -> dbAccess   "Tracks pending files via"

        organizations -> authz    "Checks privileges with"
        organizations -> dbAccess "Reads hierarchy via"

        resources -> authz    "Checks privileges with"
        resources -> dbAccess "Reads role assignments via"

        users -> loginGov   "Exchanges auth codes with (being replaced)" "OAuth 2.0 / OIDC"
        users -> grantSolutionsSso "Will authenticate users with" "" "Planned"
        users -> apiGateway "Registers user API keys with" "AWS management API"
        users -> dbAccess   "Provisions users via"

        workflowApi -> authz         "Checks privileges with"
        workflowApi -> dbAccess      "Reads workflow state via"
        workflowApi -> workflowQueue "Publishes workflow events to" "SQS API"

        healthcheck -> dbAccess   "Pings the database via"

        # ---------- Workflow worker ----------
        workflowManager -> workflowQueue "Polls events from" "SQS API"
        workflowManager -> stateMachines "Dispatches events to"
        workflowManager -> database      "Records event history in" "SQL"
        stateMachines   -> statePersistence "Saves state through"
        statePersistence -> database     "Persists workflow state in" "SQL"
        stateMachines   -> listeners     "Notifies on transitions"
        listeners       -> database      "Writes audit history to" "SQL"
        listeners       -> ses           "Sends email notifications via" "SES API"
        worker          -> newRelic      "Could forward logs to" "CloudWatch log subscription" "Planned"

        # ---------- Task runner ----------
        # The import command exists in code but is not scheduled or deployed.
        taskRunner -> samGov   "Could fetch Assistance Listings from (not deployed; source TBD)" "HTTPS" "Not Wired"
        taskRunner -> database "Upserts listings and task records in" "SQL"
        taskRunner -> cdr      "May sync Assistance Listing data with" "" "Planned"

        # ---------- File scanner ----------
        fileBucket -> scanner   "Triggers on new unscanned/ object" "S3 event"
        scanner    -> fileBucket "Moves scanned files to scanned/ or infected/ in" "S3 API"
        scanner    -> scanCache  "Updates scan status in" "DynamoDB API"
        scanner    -> files      "Reports scan results to" "HTTPS POST /v1/files/{id}, API key"

        # ---------- Deployment: network entry path ----------
        aws = deploymentEnvironment "AWS" {
            deploymentNode "AWS" "" "Amazon Web Services" {
                igw = infrastructureNode "Internet Gateway" "Entry point for all public traffic." "AWS Internet Gateway"
                cdn = infrastructureNode "CDN" "Caches and serves the frontend." "Amazon CloudFront"
                apiGatewayInstance = containerInstance apiGateway
                frontendAlb = infrastructureNode "Frontend ALB" "Routes web traffic to frontend tasks." "Application Load Balancer"
                backendAlb  = infrastructureNode "Backend ALB"  "Routes API traffic to API tasks." "Application Load Balancer"
                ssm = infrastructureNode "SSM Parameter Store" "Holds ENABLE_MAINTENANCE_MODE and MAINTENANCE_RETRY_AFTER_SECONDS." "AWS Systems Manager"

                deploymentNode "ECS Cluster" "" "ECS Fargate" {
                    taskDef = infrastructureNode "API Task Definition" "Maps SSM parameters to the API container's environment variables." "ECS task definition"
                    frontendInstance = containerInstance frontend
                    apiInstance      = containerInstance api
                    workerInstance   = containerInstance worker
                    taskRunnerInstance = containerInstance taskRunner
                }

                deploymentNode "Amazon RDS" "" "Aurora PostgreSQL cluster" {
                    databaseInstance = containerInstance database
                }
            }

            igw                -> cdn                "Routes web traffic to" "HTTPS"
            igw                -> apiGatewayInstance "Routes API traffic to" "HTTPS"
            cdn                -> frontendAlb        "Forwards to" "HTTPS"
            frontendAlb        -> frontendInstance   "Forwards to" "HTTP"
            apiGatewayInstance -> backendAlb         "Forwards to" "HTTPS"
            backendAlb         -> apiInstance        "Forwards to" "HTTP"
            # frontendInstance -> apiGatewayInstance is implied by frontend -> apiGateway.

            ssm     -> taskDef     "Read when a task launches" "ECS secrets"
            taskDef -> apiInstance "Injects as environment variables" "ECS"
        }
    }

    views {

        systemContext gm "Context" "System context for Smarter Grants Management: Opportunity (in Nava scope)." {
            include *
            autoLayout lr
        }

        container gm "Containers" "Containers and data stores that make up Opportunity." {
            include *
            autoLayout lr
        }

        # Same as ApiComponents, minus the routing edges.
        component api "ApiComponentsClean" "Components inside the API container. Authentication runs before every domain component; the routing arrows from Authentication to each domain are omitted." {
            include *
            exclude "relationship.tag==Routing"
            autoLayout lr 250 120
        }

        deployment gm aws "Deployment" "How traffic reaches the frontend and API in AWS." {
            include *
            exclude ssm taskDef
            # Hide logical container-to-container arrows; show only network hops.
            exclude "apiGatewayInstance -> apiInstance"
            exclude "apiInstance -> apiGatewayInstance"
            autoLayout lr
        }

        deployment gm aws "MaintenanceConfig" {
            title "Deployment View: Opportunity"
            include ssm taskDef apiInstance
            autoLayout lr
        }

        component api "ApiComponents" "Components inside the API container." {
            include *
            autoLayout lr 250 120
        }

        component worker "WorkerComponents" "Components inside the Workflow Worker container." {
            include *
            autoLayout lr
        }

        dynamic gm "FileUpload" "Upload a file, virus-scan it, and report the result." {
            frontend   -> apiGateway "Requests a presigned upload URL"
            apiGateway -> api        "Forwards the request"
            api        -> scanCache  "Creates a pending scan record"
            frontend   -> fileBucket "Uploads the file to unscanned/"
            fileBucket -> scanner    "Triggers the scan"
            scanner    -> scanCache  "Marks the scan in progress"
            scanner    -> fileBucket "Moves the file to scanned/ or infected/"
            scanner    -> api        "Reports the result"
            scanner    -> scanCache  "Marks the scan complete or infected"
            frontend   -> apiGateway "Streams scan results"
            apiGateway -> api        "Forwards the stream request"
            api        -> scanCache  "Polls scan status"
            autoLayout lr
        }

        dynamic gm "WorkflowEvent" "Submit a workflow event and process it asynchronously." {
            frontend -> apiGateway    "Submits a workflow event"
            apiGateway -> api         "Forwards the event"
            api      -> workflowQueue "Publishes the event"
            worker   -> workflowQueue "Polls and receives the event"
            worker   -> database      "Advances and persists workflow state"
            worker   -> ses           "Sends email notifications"
            autoLayout lr
        }

        styles {
            element "Element" {
                background #1168bd
                color #ffffff
                stroke #0b4884
            }
            element "Deployment Node" {
                background #ffffff
                color #0b4884
                stroke #0b4884
            }
            element "Infrastructure Node" {
                background #ffffff
                color #000000
                stroke #5d82a8
            }
            element "Person" {
                shape Person
                background #08427b
                stroke #052e56
            }
            element "External" {
                background #999999
                stroke #6b6b6b
            }
            element "Web" {
                shape WebBrowser
            }
            element "Database" {
                shape Cylinder
            }
            element "Queue" {
                shape Pipe
            }
            element "Lambda" {
                shape Hexagon
            }
            element "Infrastructure" {
                background #5d82a8
            }
            element "Component" {
                background #85bbf0
                color #000000
                stroke #5d82a8
            }
            element "Static" {
                background #d5e8f7
            }
            element "Not Wired" {
                border dashed
                opacity 50
            }
            element "Planned Removal" {
                stroke #c2410c
                border dashed
            }
            element "Planned" {
                background #e8f5e9
                color #1b5e20
                stroke #2e7d32
                border dashed
            }
            element "Subject to Change" {
                stroke #c2410c
                border dotted
            }
            element "Scaffolding" {
                border dashed
            }
            relationship "Planned" {
                color #2e7d32
            }
            relationship "Not Wired" {
                dashed true
                opacity 50
            }
        }
    }
}
