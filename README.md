# MlPops

A static MLOps job-market workspace: authenticated hh.ru collection, explainable classification, historical observations, personal skill gaps, and a compact Svelte interface in Russian and English. Python prepares validated JSON; the browser never calls hh.ru or receives credentials.

**Status:** review candidate. Synthetic demo is the default. No live collection, historical market coverage, model accuracy or production deployment is claimed. See [verification](docs/VERIFICATION.md), [Russian quick start](README.ru.md) and the original [specification](task_mudask.md).

## Run locally

Prerequisites: Python 3.12+, [uv](https://docs.astral.sh/uv/), Node.js 24+, npm.

```sh
uv sync --locked
uv run python -m collector demo
cd web
npm ci
npm run dev
```

Open the printed URL at `/ml_ops_vacancy/`. The explicit DEMO banner identifies fictional employers and records. The demo contains an adjacent DevOps role with genuine ML operations, generic DevOps with company-only AI, unknown salaries/work arrangements, an archived role, a salary change and a potential repost. It has **no fabricated daily market series**.

```sh
# From repository root
uv run ruff check collector analytics tests scripts
uv run ruff format --check collector analytics tests scripts
uv run pytest -q
uv run python -m collector schemas
uv run python -m collector validate web/public/data/demo.json
cd web
npm run check
npm run lint
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

The browser suite serves the **production build** at the repository subpath in an isolated local preview. It verifies both languages, refreshable query links, filtering/sidebar consistency, profiles, bookmarks, notes, comparison, cold starts, failures, and mobile overflow. Screenshots are in [docs/screenshots](docs/screenshots).

## Collect real data

Read [API access and redistribution](docs/API.md) first. A registered application token and a real developer contact are mandatory. Export environment variables using your shell or secret manager; `.env.example` is a template, not an automatically loaded file.

```sh
export HH_TOKEN='YOUR_TOKEN'
export HH_USER_AGENT='MlPops/0.1 (your-contact@your-domain.tld)'
uv run python -m collector collect --state state/real --output exports/market.json --days 30
uv run python -m collector validate exports/market.json
```

This is a private local export. Before publishing real records or state on GitHub, obtain written permission appropriate to this use and set `HH_PUBLICATION_PERMISSION` to its reference. `--public` enforces this prerequisite and removes archived/inaccessible records from public vacancy facts. It is an operator attestation, not a claim that permission exists. Do not publish private collector state into a public repository without that permission.

For an authorized local real-data build:

```sh
export HH_PUBLICATION_PERMISSION='your-written-permission-reference'
uv run python -m collector collect --state state/real --output web/public/data/market.json --days 30 --public
cd web
VITE_DATA_MODE=real BASE_PATH=/ml_ops_vacancy/ npm run build
npm run preview
```

`--days 1..90` bounds the current source publication window; it cannot recover complete historical market inventories. The collector fetches `/dictionaries` and `/areas`, partitions over 2,000-result windows to overlapping five-minute boundaries, refreshes details using a configurable TTL, and records unresolved truncation. Collection concurrency is one. Budgets, retries and timeouts are bounded. Failure does not overwrite the previous export or produce zero-count days.

## Architecture and configuration

| Path | Purpose |
| --- | --- |
| `collector/` | Contracts, HTTP client, extraction, incremental observations, CLI |
| `analytics/` | Moscow daily metrics, salary comparability, rolling-origin baselines |
| `config/searches.json` | Versioned direct and adjacent discovery queries |
| `config/taxonomy.json` | Canonical technology aliases and categories |
| `config/scoring.json` | Classifier weights/thresholds and stack assessment rules |
| `schemas/` | Export and durable-state JSON schemas |
| `web/` | Svelte 5, TypeScript, Vite, shared CSS tokens, accessible SVG charts |
| `tests/`, `web/tests/` | Synthetic offline regression and browser checks |
| `.github/workflows/` | Uncredentialed PR verification and trusted-main collection/Pages |

No backend, LLM, telemetry service or external chart runtime is required. SQLite is the reconstructed local working index; checksummed JSON on a dedicated `data` branch is durable state. See [persistence](docs/STATE.md), [methodology](docs/METHODOLOGY.md), and [deployment](docs/DEPLOYMENT.md).

The browser stores skill levels, learning goals, target roles, salary/conditions, saved filters, bookmarks, viewed/dismissed records, application statuses and notes locally. It does not sync. Personal backup import/export is separate from public filter URLs and vacancy CSV. CSV escapes spreadsheet formula prefixes.

## Deploy after review

The application stays on one feature branch and one open PR. **Do not merge automatically.** After review, merge with a single squash commit. Production Pages is only built from `main`. See [exact setup](docs/DEPLOYMENT.md) for repository settings, variables/secrets and the shared collection/deployment sequence. The initial `main` contains only the user-approved empty bootstrap commit.
