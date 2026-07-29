# Frontend — Trusted Enterprise Agent (Angular 20)

The source files (`src/app`, `src/environments`, `src/styles.scss`,
`proxy.conf.json`) are ready. They drop into a fresh Angular 20 workspace —
we don't commit `node_modules` or the generated config, we generate those
locally. One-time setup below.

## One-time setup (each teammate, ~3 min)

    # 1. Angular CLI (Node 20+ required)
    npm install -g @angular/cli@20

    # 2. Generate the workspace scaffolding IN PLACE, in this frontend/ dir.
    #    --skip-install first so we can merge our files before installing.
    cd frontend
    ng new tea-ui --directory . --style=scss --routing=false \
        --skip-git --skip-install --ssr=false

    # When prompted to overwrite src/main.ts, src/index.html, src/styles.scss,
    # app.component/app.config — say YES (our versions replace the defaults).
    # If ng refuses because the dir isn't empty, generate in a temp dir and
    # copy OUR src/ over its src/ afterwards (see "Fallback" below).

    # 3. Install dependencies
    npm install

    # 4. Run against the backend (backend must be up on :8000)
    npm start -- --proxy-config proxy.conf.json

Open http://localhost:4200. Ask a question, then hit "Run evaluation".

## Fallback if `ng new` won't scaffold into a non-empty dir

    cd ~/PROJECTs/jivs-hackathon-2026
    mv frontend frontend-src            # our source, temporarily aside
    ng new frontend --directory frontend --style=scss --routing=false --ssr=false
    cp -a frontend-src/src/. frontend/src/
    cp frontend-src/proxy.conf.json frontend/
    rm -rf frontend-src
    cd frontend && npm start -- --proxy-config proxy.conf.json

## Wire the proxy into `npm start` permanently (optional)

In `angular.json`, under `projects > <name> > architect > serve > options`, add:

    "proxyConfig": "proxy.conf.json"

Then plain `npm start` uses the proxy.

## What's here

    src/app/core/models.ts        TypeScript mirrors of the backend responses
    src/app/core/api.service.ts   single gateway to the FastAPI backend
    src/app/features/chat/        agent console: question -> cited answer + badges
    src/app/features/metrics/     live eval panel (PII F1, catch rate, zero-leak)
    src/styles.scss               theme tokens (JiVS gold on ink)
    src/environments/             dev (proxy) vs prod (deployed API URL)
    proxy.conf.json               dev proxy -> localhost:8000 (avoids CORS)

## Angular version note

Written for Angular 20: standalone components, signals, new control flow
(`@if`/`@for`), zoneless change detection. If the event pins a different
major, the only likely fixes are `provideZonelessChangeDetection` (name
changed across versions) and the control-flow syntax. Keep this in mind
if we must match a JiVS-specified version on the day.
