# Deploying the AEGIS frontend to Vercel

The public site is the landing page plus a demo-mode console: it serves a few
captured real agent responses so it stays live and free, with a "run locally"
note linking to the repo. No backend is deployed.

## One-time: enable prod environment swap

Angular must swap `environment.ts` for `environment.prod.ts` in production so
`demoMode` becomes `true`. Confirm this block exists in `angular.json` under
`projects > frontend > architect > build > configurations > production`
(Angular 20 usually generates it; add it if missing):

    "fileReplacements": [
      {
        "replace": "src/environments/environment.ts",
        "with": "src/environments/environment.prod.ts"
      }
    ]

Verify locally before deploying:

    npm run build            # production build by default in Angular 20
    npx http-server dist/frontend/browser   # open the served URL, /app should
                                            # show the "Live preview" banner

## Deploy

1. Push the repo to GitHub (already done).
2. On vercel.com: New Project -> import the GitHub repo.
3. Set the **Root Directory** to `frontend` (the Angular app lives there).
4. Vercel reads `vercel.json`: build `npm run build`, output
   `dist/frontend/browser`, SPA rewrites to `index.html`. Framework preset:
   Angular (or "Other" — vercel.json covers it).
5. Deploy. Vercel gives an https URL like `aegis-<you>.vercel.app`.

## After deploy

- Put the live URL in the main README badge/link.
- The console works with the five saved examples; other questions show the
  run-locally note. This is intentional and costs nothing.
- Update `repoUrl` in both environment files if the repo moves.
