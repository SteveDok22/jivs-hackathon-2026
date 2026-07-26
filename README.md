# Trusted Enterprise Agent — JiVS Hackathon 2026

Secured AI agent over cleansed enterprise data.
Core bet: one system covers the four most likely challenge topics
(historical-data agent, PII protection, guardrails, data sovereignty).

## Architecture (5 layers)

    query -> [1 input filter] -> [3 agent: schema retrieval + SQL policy]
                                       |
                    [2 data layer: pseudonymized data only]
                                       |
             [4 output PII scan] -> answer with citations
                                       |
                        [5 live eval metrics panel]

## Repository layout

    backend/            FastAPI application (Python 3.12)
      app/
        main.py         app entry point, routers are plugged here
        config.py       all settings, single source of truth
        api/routes/     HTTP endpoints (Stage 0: /health)
      tests/            pytest suite, mirrors app structure
    frontend/           Angular workspace (generated in Stage 7)
    .github/workflows/  CI: ruff + pytest on every push
    docker-compose.yml  local stack: api + postgres

## Quick start

    cp .env.example .env
    docker compose up --build
    curl http://localhost:8000/health

Interactive API docs: http://localhost:8000/docs

## Run tests locally (without Docker)

    cd backend
    python3 -m venv .venv && source .venv/bin/activate
    pip install -e ".[dev]"
    pytest -v

## Roadmap

| Stage | Module | Status |
|-------|--------|--------|
| 0 | Repo skeleton, /health, CI | done |
| 1 | LLM client (Claude/Bedrock switch, model cascade, cost meter) | done |
| 2 | Data connectors + synthetic SAP-like dataset with ground truth | done |
| 3 | PII module: detection, fuzzy search, deterministic pseudonymization | done |
| 4 | Agent: schema retrieval, SQL generation, sqlglot policy, citations | done |
| 5 | Guardrails: injection filter (in), PII scan (out) | next |
| 6 | Eval panel: golden dataset, live metrics | |
| 7 | Angular frontend | |
| 8 | AWS deploy, pitch deck, rehearsal | |
