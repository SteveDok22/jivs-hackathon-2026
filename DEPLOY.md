# Deployment & Hackathon-Day Runbook

Goal from the strategy doc: **/health answering in the cloud within hour one**,
so the pipeline is proven and the team spends the 24 hours on the task.

## Local full stack (rehearse this before the event)

    cp .env.example .env          # fill ANTHROPIC_API_KEY
    docker compose -f docker-compose.full.yml up --build
    # API:      http://localhost:8000/health
    # Frontend: http://localhost:8080

This is the fallback demo environment: even with no cloud, the whole product
runs on one laptop from one command.

## AWS (sponsor points — deploy here if credits arrive)

Two paths, simplest first.

### Option A — AWS App Runner (fastest, recommended for 24h)
App Runner takes a container image and gives back an HTTPS URL. No cluster to
manage.

1. Build and push the API image to ECR:

       aws ecr create-repository --repository-name tea-api
       docker build -t tea-api ./backend
       # tag & push per the ECR "push commands" shown in the console

2. Create an App Runner service from the ECR image, port 8000,
   env var `ANTHROPIC_API_KEY` (or switch to Bedrock — see below).
3. Repeat for the frontend image (port 80), or host the built static files
   on S3 + CloudFront.

### Option B — ECS Fargate (more control, more setup)
Use only if App Runner is unavailable. Task definition with two containers
(api, frontend), an Application Load Balancer, target groups on 8000 and 80.

### Switch to Bedrock (sponsor points, no voucher needed)
In `.env` on the deployed service:

    LLM_PROVIDER=bedrock
    AWS_REGION=eu-central-1
    BEDROCK_FAST_MODEL_ID=...      # copy exact IDs from the Bedrock console
    BEDROCK_SMART_MODEL_ID=...

No code change — the provider switch is config only (proven in Stage 1).
Give the App Runner / Fargate task role `bedrock:InvokeModel` permission.

## Hackathon-day runbook (the first 90 minutes)

1. **Clone + boot** (all members): `docker compose up --build`, confirm
   `/health` and `pytest` green. 10 min.
2. **One person**: push API image to ECR, stand up App Runner, confirm the
   cloud `/health`. This de-risks deploy while others read the task. 30 min.
3. **Read the actual challenge.** Map it to the nearest prepared topic
   (T1/T2/T4/T5 -> core is ready; T3 -> refactor spare; else -> core plumbing).
4. **Point the data layer at their data.** Export their tables to CSV or
   connect via the SQL connector; regenerate the schema catalog. 20 min.
5. **Wire the task-specific logic only.** Everything else already runs.
6. **Turn on the eval panel** against their data; start collecting numbers.

## Pre-event checklist (do the week before)

- [ ] Node 20 LTS via nvm on every laptop (current v25 is non-LTS).
- [ ] `docker compose -f docker-compose.full.yml up` works end to end.
- [ ] AWS account with CLI configured; ECR repos created; App Runner tried once.
- [ ] spaCy model en_core_web_sm installed (`python -m spacy download en_core_web_sm`); AdventureWorks downloaded.
- [ ] ODBC Driver 18 installed (Azure SQL access, their 2025 setup).
- [ ] Each member has run the full test suite once and seen the eval report.
- [ ] Pitch deck skeleton filled with our real numbers.
