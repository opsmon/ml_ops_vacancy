# GitHub Actions and Pages

## Review gate

All implementation is on `feat/mlpops`; leave its PR open for review. An empty `main` bootstrap was explicitly approved by the user because the repository had no initial commits. Do not push application commits directly to main, automatically merge, or publish this initial implementation before review. PR CI serves the production static build in its own isolated browser-test server and uploads a candidate artifact with screenshots and file checksums; it does not have collection secrets or production permissions.

After required CI and candidate review, a maintainer can squash-merge the single PR. The production workflow is restricted to `github.ref == refs/heads/main` and checks out `main`. Fork PRs execute only the uncredentialed CI workflow. There is no `pull_request_target` workflow.

## Repository setup

1. In **Settings → Actions → General**, enable GitHub Actions and permit the official actions used here. The workflow grants narrowly scoped job permissions itself; an organization policy can still restrict writes.
2. In **Settings → Pages → Build and deployment → Source**, choose **GitHub Actions**. No `gh-pages` content branch is used. `data` is only durable collection state.
3. In **Settings → Environments → github-pages**, restrict production deployment branches to `main`. Add required reviewers if your account supports them.
4. In **Settings → Branches / Rulesets**, protect `main`, require the **Candidate verification / verify** check and review, and allow squash merges. The repo must have the feature PR's workflow available to run that check.
5. Initially leave `DATA_MODE` unset or set to `demo` in **Settings → Secrets and variables → Actions → Variables**. The first reviewed deployment will explicitly display synthetic data.
6. For authorized real publication only, add secret `HH_TOKEN`; variables `HH_USER_AGENT` (app/version and real email), `HH_PUBLICATION_PERMISSION` (written permission reference) and optionally `HH_REQUEST_BUDGET` (default 800). Do not put token secrets in Vite variables.
7. Run **Refresh and publish Pages** on main with **refresh=true** and a bounded 1–90-day lookback. A successful run persists validated `data` state and `public/market.json`. Once a real authorized export exists, set `DATA_MODE=real` and run the workflow. No credentials/permission/export means real publication stays blocked, never demo fallback.

The expected repository-path URL is `https://opsmon.github.io/ml_ops_vacancy/`. **This is an expected URL, not evidence of deployment.** A verified deployment URL must come from the successful deploy job. The PR remains open at delivery; production is pending review/merge. Pages was configured to use Actions during implementation; no initial production deployment was started.

## State flow and triggers

`Candidate verification`: feature pushes and PRs to main; locked Python/Node dependencies; lint, Python tests, generated-schema check, demo validation, Svelte/TypeScript check, ESLint, Vitest, production build and Playwright desktop/mobile. It records candidate SHA, per-file SHA-256 and a tree digest in its artifact and job summary.

`Refresh and publish Pages`: main pushes, manual dispatch and `17 1,7,13,19 * * *` **UTC** (04:17, 10:17, 16:17, 22:17 Europe/Moscow). Scheduled collection runs only with `DATA_MODE=real`; synthetic demo is deterministic, never periodically fabricated. Manual dispatch supports explicit refresh and bounded source lookback.

A single shared non-canceling concurrency group serializes state fetch, collection, commit and deployment. The job restores the `data` worktree, reconstructs SQLite, collects and validates, then commits partitioned text state plus the validated export. Failure reports are committed even on failed collection. Failed collection stops the build/deploy, preserving the previous public artifact/site. State push is a normal fast-forward push; conflicts fail rather than overwrite another writer.

The **same run** builds from the newly validated data (or selected existing valid export), configures Pages, uploads the official Pages artifact and deploys it using Pages/OIDC permissions and the `github-pages` environment. It never relies on a `GITHUB_TOKEN` data commit triggering another workflow. Deploy performs index and dataset HTTP health checks; inspect the uploaded evidence and deployment job URL afterward.

Current official action releases checked through the GitHub API on 2026-10-22: checkout 7.0.1; setup-node 7.1.0; setup-python 7.1.0; upload-artifact 7.0.2; configure-pages 6.0.0; upload-pages-artifact 5.0.0; deploy-pages 5.0.1. Official [custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) describes the permissions and job dependencies. Versions are exact release tags; dependency upgrades should be reviewed through a PR.

## Paths, routing and domain

Vite's default base is `/ml_ops_vacancy/`. Production uses `configure-pages.outputs.base_path`, which also accommodates custom-domain root hosting. `BASE_PATH=/` supports a local/root build. Runtime JSON is fetched from `import.meta.env.BASE_URL`, never a hard-coded origin. State/navigation is query-string based; direct links and refreshes require no server-side route rewriting. Language persists in the URL and localStorage, with URL priority. Personal data is never serialized into links.

For a custom domain configure it in Pages, configure DNS, and add the appropriate `web/public/CNAME` if your deployment policy requires it. Do not set a domain during candidate review. Use the Pages action's returned base path after the setting is in place.

## Scheduler and rollback limits

GitHub [scheduled events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) run from the default branch, can be delayed/dropped under load, and public repositories can have schedules disabled after 60 days of inactivity. Four runs are intended, not guaranteed. The UI displays actual freshness and coverage. Re-enable disabled scheduling in Actions and check run logs if freshness degrades.

Rollback app code via a reviewed revert PR, or redeploy an already verified prior main revision according to repository policy. Keep the data branch's last valid commit before migrations. Do not reset published branch history. A failed refresh does not require rollback of a healthy existing site. There are no production database migrations or shared services in this static architecture.
