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

## Debugging & Fixes

Real issues encountered while building this project and how they were resolved.
Kept as an engineering log — each entry is a symptom, the root cause, and the fix.

**1. Duplicate LLM layer (Stage 1).**
*Symptom:* two parallel implementations of the LLM client appeared in `app/llm/`
(a `base.py`/`factory.py`/`pricing.py` set alongside `client.py`/`cost.py`).
*Cause:* a stray earlier iteration left behind a second module set; either could
be imported, risking hard-to-trace bugs at runtime.
*Fix:* kept one implementation, merged the two good ideas from the other
(substring-based pricing keys, a cached client factory), deleted the rest so the
codebase has exactly one LLM path.

**2. `setuptools` multiple-packages error (Stage 2).**
*Symptom:* `pip install -e .` failed with *"Multiple top-level packages discovered
in a flat-layout: ['app', 'data']"*.
*Cause:* generating the dataset into `backend/data/` made setuptools see a second
top-level package and refuse to guess which to build.
*Fix:* pinned discovery to the real package with
`[tool.setuptools.packages.find] include = ["app*"]`.

**3. PII recall stuck at 0.75 (Stage 3).**
*Symptom:* four ground-truth occurrences were missed — all names hidden in free
text with typos or cross-language spellings ("Paul Jnoas", "Kowaljow").
*Cause:* `token_set_ratio` over the whole sentence collapses when the misspelled
token drops out of the exact-token intersection; and Latin/Cyrillic/German
spellings of one name scored near zero.
*Fix:* added a sliding-window fuzzy match at the target's token width, plus
transliteration folds (w->v, j->y) applied to both sides of every comparison.
Recall went to 1.00 on the golden set.

**4. DuckDB `CREATE VIEW` with a bound parameter (Stage 2).**
*Symptom:* building views over the CSV files threw a binder error.
*Cause:* DuckDB does not accept prepared-statement parameters in `CREATE VIEW`.
*Fix:* switched to an escaped string literal for the file path (still safe — the
value is a local filename, not user input).

**5. Model string 404 risk (Stage 9).**
*Symptom:* the smart-tier model was `claude-sonnet-4-6`, which would fail once a
real API key was used.
*Cause:* the current model is `claude-sonnet-5` (released 2026-06-30); the code
carried an outdated string.
*Fix:* updated the config default and pricing table; verified against current
Anthropic pricing.

**6. Container ran stale code — `ModuleNotFoundError: sqlglot` (Stage 4, live).**
*Symptom:* the API container crash-looped; `/health` and `/eval` hung.
*Cause:* new dependencies were added to `pyproject.toml`, but the container was
restarted with `docker compose up` (no `--build`), so the image predated them.
*Fix:* rebuild with `docker compose up -d --build` after any dependency change —
now a documented rule.

**7. Env var not picked up after editing `.env` (live).**
*Symptom:* agent calls failed with *"Could not resolve authentication method"*
even though `ANTHROPIC_API_KEY` was set in `.env`.
*Cause:* `docker compose restart` reuses the existing container's environment; it
does not re-read `env_file`.
*Fix:* use `docker compose up -d --force-recreate api` to recreate the container
and reload `.env`.

**8. Valid `COUNT(*)` query rejected by the policy (Stage 10).**
*Symptom:* `SELECT COUNT(*) FROM kna1` was blocked with *"SELECT * is not allowed"*.
*Cause:* the policy flagged any `Star` node, not distinguishing a bare
`SELECT *` projection from a `COUNT(*)` aggregate.
*Fix:* only reject a star whose parent is the SELECT itself; stars inside function
calls (COUNT and other aggregates) are allowed.

**9. Valid table rejected as "not on allowlist" (Stage 10).**
*Symptom:* `SELECT COUNT(*) FROM kna1` failed with *"table not on allowlist: kna1"*
even though `kna1` is a real table.
*Cause:* the policy allowlist was built from the top-k *retrieved* schema cards, so
a valid query was rejected whenever retrieval ranked the right table below the cut.
*Fix:* separated concerns — retrieval decides what schema to *show* the model, but
the allowlist is the *full* catalog of real tables. Also boosted exact
table-name mentions in retrieval so short names like `kna1` surface reliably.

**10. Wrong relative-import depth in a shared component (Stage 18).**
*Symptom:* the hero demo component imported `../../core/api.service`, which
escapes the `app/` directory — a build-time module-not-found.
*Cause:* the path was copied from a `pages/*` component (two levels deep) into a
`shared/*` component (one level deep), so it needed `../core`, not `../../core`.
*Fix:* corrected the depth; verified every import across the frontend resolves
to a real file with a path-checking script.

## Roadmap

| Stage | Module | Status |
|-------|--------|--------|
| 0 | Repo skeleton, /health, CI | done |
| 1 | LLM client (Claude/Bedrock switch, model cascade, cost meter) | done |
| 2 | Data connectors + synthetic SAP-like dataset with ground truth | done |
| 3 | PII module: detection, fuzzy search, deterministic pseudonymization | done |
| 4 | Agent: schema retrieval, SQL generation, sqlglot policy, citations | done |
| 5 | Guardrails: injection filter (in), PII scan (out) | done |
| 6 | Eval panel: golden dataset, live metrics | done |
| 7 | Angular frontend (chat + citations, live metrics panel) | done |
| 8 | AWS deploy (Dockerfile, App Runner), pitch deck, runbook | done |
| 9 | Legacy refactoring: screenshot -> Angular, self-check fidelity loop | done |
| 10 | Agent polish: COUNT(*) allowed, allowlist = full catalog, name-boosted retrieval | done |
| 11 | Real Presidio NER: person discovery (169 names found), model in image + CI | done |
| 12 | Fidelity metric in eval panel + discovery/refactor cards in frontend | done |
| 13 | AEGIS design system: DESIGN.md + theme tokens (dark/red/neon-white) | done |
| 14 | Two-page skeleton: routing (/ + /app), Line Sidebar nav, product console | done |
| 15 | Plexus network background: red data-net, cursor repel, scan pulse (canvas 2D) | done |
| 16 | Hero: animated five-layer diagram, live demo field, title entrance (Anime.js) | done |
| 17 | Landing sections: scroll-reveal, count-up metrics, Grid Scan, full content | done |
| 18 | Custom cursor, product-page background, footer, polish | done |
| 19 | Sidebar overlap fix, animated eval reveal (shutter + count-up), live scan field | done |
