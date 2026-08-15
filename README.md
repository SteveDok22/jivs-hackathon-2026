# AEGIS — Trusted Enterprise AI

**Trusted Enterprise AI, built for secure organizations.**

AEGIS is a secured AI agent that answers plain-language questions over an
enterprise data archive — and does it safely enough to run on real data. Every
answer is cited back to its source rows, every database access is checked
against an explicit policy, personal data is pseudonymized before the model
ever sees it, and prompt-injection attempts are filtered out. The name is the
Greek *aegis*, the shield of Zeus: the whole system is a shield over live data.

🔗 **Live site:** _[ soon — deployed on Vercel]_
📦 **Repository:** https://jivs-hackathon-2026.vercel.app/

> The hosted site is a **live preview**: the landing page is fully interactive,
> and the console runs a set of captured real agent responses so it stays live
> and free. The full agent — your own questions, live evaluation, the whole
> five-layer pipeline — runs locally from this repo (see **Deployment**).

---

## Table of Contents

- [About](#about)
- [Screenshots](#screenshots)
- [Architecture](#architecture--the-five-layers)
- [Dataset Content](#dataset-content)
- [Business Requirements](#business-requirements)
- [Hypotheses and Validation](#hypotheses-and-validation)
- [The Rationale: Requirements to Layers](#the-rationale-mapping-requirements-to-layers)
- [AI / Agent Business Case](#ai--agent-business-case)
- [Evaluation and Metrics](#evaluation-and-metrics)
- [Console Design](#console-design)
- [Debugging & Fixes](#debugging--fixes)
- [Deployment](#deployment)
- [Main Libraries and Tech Stack](#main-libraries-and-tech-stack)
- [Credits](#credits)

---

## About

Companies archive legacy systems into a data vault and switch the old system
off. The data survives, but it is effectively locked: answering a simple
question means knowing the right tables out of thousands and writing SQL by
hand. Pointing a naive AI at that data is not an option either — it holds
personal information, and an unguarded model can be tricked into leaking it or
running destructive queries.

AEGIS solves both halves at once: a natural-language agent that makes the
archive usable, wrapped in five layers of protection that make it safe. It was
built originally as preparation for the JiVS Hackathon 2026 (an enterprise data
platform), then continued as a portfolio project.

**Two surfaces:**
- A **landing page** that explains the product with a live plexus-network
  background, an animated five-layer diagram, count-up metrics, and a live demo.
- A **console** (`/app`) — the working agent: ask a question, watch it get
  filtered, checked, answered with citations, and scored on a live metrics panel.

---

## Screenshots

> _Add screenshots here after deployment (captured from the production build)._

| View | Description |
|------|-------------|
| _Hero_ | Landing page with plexus background and animated five-layer flow |
| _Console_ | The agent answering with cited source rows |
| _Policy refusal_ | A restricted-column request being refused |
| _Injection blocked_ | A prompt-injection attempt caught at the input filter |
| _Evaluation panel_ | Live metrics: detection F1, catch rate, discovery, cost |

---

## Architecture — The Five Layers

> _A live architecture diagram will be added here._

A request flows left to right through five layers; break one and the next still
holds — defense in depth, not a single gate.

```
  ┌─────────────┐   ┌──────────────┐   ┌───────────────┐   ┌─────────────┐   ┌──────────────┐
  │ 1. Input    │──▶│ 2. Pseudonymized │─▶│ 3. Policy-bound │─▶│ 4. Output   │─▶│ 5. Cited     │
  │    filter   │   │    data       │   │    agent      │   │    scan     │   │    answer    │
  └─────────────┘   └──────────────┘   └───────────────┘   └─────────────┘   └──────────────┘
   blocks prompt     names replaced,     SQL parsed &         no PII leaves      every claim
   injection         joins intact        checked before run   the system         sourced
```

1. **Input filter** — layered heuristics (plus an optional classifier) catch
   prompt-injection attempts before the agent runs.
2. **Pseudonymized data** — the model only ever sees masked data: names are
   replaced deterministically and consistently across tables, so joins and
   statistics still work.
3. **Policy-bound agent** — generated SQL is parsed with `sqlglot` and checked
   against an explicit allowlist/denylist before it touches the database. The
   model has no direct database access.
4. **Output scan** — the answer is scanned on the way out; any restricted PII is
   redacted even if an earlier layer let it through.
5. **Cited answer** — every answer carries the exact tables and rows it came
   from, so it can be trusted and verified.

---

## Dataset Content

Because a real enterprise archive cannot be shared, AEGIS ships with a
**synthetic SAP-like dataset** generated deterministically (`seed=42`) so the
whole system — and its evaluation — is reproducible by anyone.

The generator (`backend/app/data/synthetic.py`) produces real SAP table names:

| Table | Meaning | Key columns |
|-------|---------|-------------|
| `KNA1` | Customer master | KUNNR (id), NAME1, ORT01 (city), STRAS, TELF1*, SMTP_ADDR* |
| `LFA1` | Vendor master | LIFNR (id), NAME1, ORT01, STRAS |
| `BKPF` | Accounting document header | BELNR, GJAHR (year), BLART |
| `BSEG` | Accounting document line items | BELNR, WRBTR (amount), SGTXT |

`*` `TELF1` (phone) and `SMTP_ADDR` (email) are marked **restricted** — the
policy layer refuses any query that selects them.

The generator also writes a `ground_truth.json` — a known answer key of where
personal names appear (including deliberately tricky cases: cross-language
spellings like "Yuri Kovalev" / Cyrillic, and typo'd variants) so PII detection
can be scored precisely. 150 customers, matching vendors, and multi-year
accounting documents give the agent realistic aggregate questions to answer.

---

## Business Requirements

The system was designed around four requirements, drawn from the kinds of
challenges an enterprise data platform poses:

1. **Make the archive usable.** A non-technical user must be able to ask a
   question in plain language and get a correct, sourced answer without knowing
   the schema or writing SQL.
2. **Protect personal data.** Personal information must never reach the model in
   raw form, and must never leak out in an answer — while the data stays usable
   for legitimate analysis.
3. **Enforce access policy.** Some columns and operations are off-limits. The
   system must enforce this deterministically, not rely on the model's goodwill.
4. **Resist misuse.** Prompt-injection and destructive-query attempts must be
   caught, and the system must be honest about what it refused and why.

---

## Hypotheses and Validation

**H1 — Deterministic pseudonymization keeps data usable.**
*Hypothesis:* replacing each person with one consistent fake identity across all
tables protects privacy without breaking joins or statistics.
*Validation:* the eval harness pseudonymizes the dataset and confirms **zero**
original PII tokens leak, while joins across pseudonymized tables still resolve —
16 cells replaced, data still queryable.

**H2 — A parser-enforced policy beats prompting.**
*Hypothesis:* checking generated SQL with a real parser is more reliable than
asking the model to behave.
*Validation:* restricted-column and non-SELECT queries are refused at the policy
layer regardless of what the model generates — demonstrated live (e.g. an email
request refused with `restricted column: SMTP_ADDR`).

**H3 — Layered guardrails catch injection without over-blocking.**
*Hypothesis:* heuristic input filtering can catch attacks while leaving normal
questions alone.
*Validation:* **100% catch rate** (12/12 attack corpus) with **0% false
positives** (0/5 benign), measured by the harness.

**H4 — Statistical NER finds people the watch-list misses.**
*Hypothesis:* Presidio NER discovers personal names beyond a known list.
*Validation:* against a 3-name watch-list, discovery finds **169 distinct
persons** across the dataset — the "find all names" capability regex cannot
provide.

---

## The Rationale: Mapping Requirements to Layers

| Business requirement | Layer(s) that satisfy it | How |
|----------------------|--------------------------|-----|
| Make the archive usable | Agent (3) + Cited answer (5) | schema retrieval + SQL generation, every answer sourced |
| Protect personal data | Pseudonymized data (2) + Output scan (4) | mask before the model; scan after it |
| Enforce access policy | Policy-bound agent (3) | `sqlglot` parses SQL, checks allowlist/denylist before execution |
| Resist misuse | Input filter (1) + Policy (3) | injection heuristics in; single-SELECT-only enforced |

Every requirement maps to at least two layers, so no single failure exposes the
data — the core of the "defense in depth" argument.

---

## AI / Agent Business Case

**Why an agent, not just text-to-SQL?** The value is not only translating a
question to SQL — it is doing so *safely and verifiably*. AEGIS retrieves the
relevant schema (so it scales past thousands of tables without stuffing the
prompt), generates SQL, has that SQL independently checked, executes it against
pseudonymized data, and returns the answer *with its sources*.

**Model cascade for cost.** A two-tier cascade routes cheap, frequent work to a
fast model and reserves the stronger model for SQL generation:
- `Tier.FAST` → Claude Haiku 4.5 (input filtering, light tasks)
- `Tier.SMART` → Claude Sonnet 5 (SQL generation, structured extraction)

A `CostMeter` records token usage and dollar cost per request, surfaced in the
UI. Critically, the **entire PII path is LLM-free** (regex + Presidio + fuzzy
matching), so pseudonymizing 1000 records costs **$0** — the model is used only
where it adds value.

**Provider-agnostic.** The LLM client switches between the Anthropic API and
AWS Bedrock by configuration alone (no code change), so the same system can run
on a cloud provider's managed models when required.

---

## Evaluation and Metrics

AEGIS does not claim it works — it measures it. The eval harness
(`backend/app/eval/harness.py`) runs entirely offline against the synthetic
dataset and its ground-truth key, and reports:

| Metric | Result | Meaning |
|--------|--------|---------|
| PII detection F1 | **1.00** | precision 1.00 / recall 1.00 on the golden name set |
| Names discovered (NER) | **169** | distinct persons found by Presidio, vs a 3-name watch-list |
| Injection catch rate | **100%** | 12/12 attacks caught, 0/5 benign wrongly blocked |
| Data safety | **Zero leak** | no original PII survives pseudonymization (16 cells replaced) |
| Cost / 1000 records | **$0.00** | the PII path is entirely LLM-free |
| Refactor verifier | **Correct** | the self-check fidelity loop scores its own output correctly |

Run it yourself: `python -m app.eval`, or `POST /eval/run`, or hit **Run
evaluation** in the console.

**Bonus capability — legacy refactoring.** A separate module turns a screenshot
of a legacy screen into a modern Angular component, then *verifies its own
output*: it re-derives a UI spec from the generated code, compares it to the
original, scores fidelity, and refines if it falls short. The fidelity verifier
is checked in the eval panel.

---

## Console Design

The console (`/app`) is where the agent lives. Design decisions:

- **Provenance first.** Every answer leads with its security verdicts (verified /
  policy-refused / injection-blocked / PII-redacted) and shows the SQL executed
  and the cited source rows. Trust is the point, so it is the most prominent thing.
- **Guided examples.** Five curated questions with category badges (Normal,
  Aggregate, PII search, Blocked by policy, Injection blocked) let a first-time
  user experience every facet of the system in five clicks.
- **Live evaluation.** A metrics panel runs the harness and reveals the results
  with an animated shutter-and-count-up, so the numbers feel earned.
- **Live-preview mode.** On the hosted site (no backend), the console serves
  captured real responses and clearly labels itself a preview, linking to the
  repo for the full local experience.

The visual language (dark base, red as the signal colour for data and threats,
neon-white for verified/outlined state) is documented in `frontend/DESIGN.md`.


---

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

**11. Required directive input used as a bare marker broke the build (Stage 19).**
*Symptom:* `ng serve` failed with `TS2322: Type 'string' is not assignable to
type 'number'` on `appCountUp [appCountUp]="169"`, and the dev server never
started.
*Cause:* the count-up directive declares `appCountUp` as
`input.required<number>()`. Writing it twice — once as a bare attribute marker
and once as a bound input — made Angular bind the bare marker as an empty
string to a number-typed required input.
*Fix:* use the input binding alone (`[appCountUp]="169"`); the directive still
activates from the bound input, no separate marker needed. Unlike a bare
`appReveal` (which has a default value and so tolerates the marker form), a
required input must always receive its typed value.

**12. Untyped `ElementRef` injection broke the strict-mode build (Stage 19).**
*Symptom:* `ng serve` failed with a cluster of `TS7006: Parameter implicitly has
an 'any' type` and `TS2347: Untyped function calls may not accept type
arguments` across the animation components.
*Cause:* `inject(ElementRef<HTMLElement>)` does not convey the element type —
`inject` returned `ElementRef<any>`, so `nativeElement` was `any`, which poisoned
every `querySelector<HTMLElement>` and `.forEach` callback downstream.
*Fix:* type the injection explicitly with
`inject<ElementRef<HTMLElement>>(ElementRef)` in every component/directive, give
`querySelector<HTMLElement>` results proper element fields, and annotate the
Anime.js `update` callback. Now `nativeElement` is typed and the strict compiler
infers the rest.

**13. Interpolation into `data-*` and bare directive inputs broke the template build (Stage 19).**
*Symptom:* `NG8002: Can't bind to 'count'` on `data-count="{{ expr }}"`, plus
`TS2322: string not assignable to number` on bare `appReveal`.
*Cause:* Angular parses `data-x="{{ expr }}"` as a property binding (there is no
`count` property), and a bare structural-style input on a number-typed directive
binds the empty string under the strict template compiler.
*Fix:* use `[attr.data-count]="expr"` for dynamic data attributes, and give the
reveal directive an input `transform` that coerces `number | string` to a
number — so both `appReveal` and `[appReveal]="80"` type-check.

**14. Customer IDs falsely redacted as phone numbers (Stage 22).**
*Symptom:* an answer mentioning a customer number (`0000001063`) came back with
that value replaced by `[REDACTED_PHONE]` — the output PII scan mistook an ID
for a phone number.
*Cause:* the phone regex matched any run of 9+ digits, so bare identifiers with
no separators were caught.
*Fix:* require a phone to start with `+` or contain a real separator (space,
dash, slash, parens); bare digit runs are treated as IDs. Regression tests
cover both an ID (not matched) and real phones (still matched).


## Deployment

The two parts deploy separately — this is deliberate.

### Frontend (public, live) — Vercel

The landing page and demo-mode console are static after build, hosted free on
Vercel. See `frontend/DEPLOY-VERCEL.md` for the full walkthrough. In short:

1. Import the GitHub repo on vercel.com, set **Root Directory** to `frontend`.
2. `vercel.json` supplies the build command, output directory, and SPA rewrites.
3. Ensure `angular.json`'s production config has the `fileReplacements` block
   that swaps in `environment.prod.ts` (enables demo mode).
4. Deploy — Vercel returns an https URL.

### Backend (local) — Docker

The full agent runs locally. Requires an `ANTHROPIC_API_KEY`.

```bash
git clone https://github.com/SteveDok22/jivs-hackathon-2026
cd jivs-hackathon-2026
cp .env.example .env          # add your ANTHROPIC_API_KEY
docker compose up -d --build
docker compose exec api python -m app.data.synthetic --out data/synthetic --seed 42
curl http://localhost:8000/health
```

Then run the frontend against it in dev mode (live, not demo):

```bash
cd frontend
npm install
npm install animejs@3.2.2 && npm install -D @types/animejs@3.1.12
npm start -- --proxy-config proxy.conf.json     # http://localhost:4200
```

### Run tests

```bash
cd backend
pip install -e ".[dev]"
python -m spacy download en_core_web_sm     # for Presidio NER tests
pytest -q                                    # 63 passing
```

---

## Main Libraries and Tech Stack

**Backend**
- **FastAPI** + **Pydantic v2** — API and typed models
- **Anthropic Claude API** (Haiku 4.5 / Sonnet 5) with an AWS **Bedrock** switch
- **Presidio** + **spaCy** (`en_core_web_sm`) — statistical PII / name detection
- **sqlglot** — SQL parsing and the policy barrier
- **DuckDB** + **SQLAlchemy** — querying CSV-backed tables
- **rapidfuzz** — fuzzy name matching; **Faker** — deterministic pseudonyms
- **pytest** + **ruff** — 63 tests, linting; **Docker** — containerization

**Frontend**
- **Angular 20** — standalone components, signals, zoneless change detection
- **Anime.js** — the five-layer animation, count-ups, shutter reveals
- **Canvas 2D** — the plexus network background (lighter than WebGL, identical result)
- **TypeScript**, **SCSS** with a tokenized design system

---

## Credits

- Built by **Stiven** ([SteveDok22](https://github.com/SteveDok22)) as a
  portfolio project, developed from JiVS Hackathon 2026 preparation.
- Synthetic dataset uses real SAP table names for realism; all data is generated
  and fictional.
- The plexus background was inspired by particle-network visualizations and
  rebuilt from scratch in canvas 2D.
- Design language and engineering decisions are documented inline and in
  `frontend/DESIGN.md`.

---

_This project is a demonstration of secure AI-agent architecture. The hosted
site is a live preview; the full pipeline runs locally._
