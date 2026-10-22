You are a senior full-stack engineer, data engineer, and product designer. Build **MlPops**, a complete job market intelligence application focused on MLOps, ML infrastructure, AI platforms, and adjacent DevOps/SRE opportunities on hh.ru.

Implement the application, data pipeline, tests, documentation, and GitHub Pages deployment workflows. Do not stop after writing a plan or creating a UI mockup.

## 1. Product purpose

MlPops helps a DevOps engineer answer:

- Which MLOps opportunities are available?
- Which DevOps/SRE vacancies include meaningful ML infrastructure responsibilities?
- What technologies and experience do employers actually require?
- Which jobs match my current skills?
- What should I learn to become eligible for more positions?
- How many relevant vacancies were discovered or published today?
- Is demand growing or declining?
- How many new relevant vacancies might appear tomorrow?
- Which employers are hiring repeatedly?
- Which vacancies have changed since my last visit?

The primary interface language is Russian. Keep source code identifiers and technical documentation in English. Include a useful Russian README or Russian quick-start section.

Product name: **MlPops**.
Suggested tagline: **«Радар вакансий и технологий MLOps»**.

## 2. Architecture and stack

Use a practical architecture suitable for GitHub Pages:

- Python for collection, normalization, extraction, classification, analytics, and forecasting.
- React, TypeScript, and Vite for the frontend.
- Tailwind CSS or an equivalent maintainable styling approach.
- A suitable chart library such as Recharts.
- SQLite as the local pipeline database.
- Versioned, validated JSON exports consumed by the static frontend.
- GitHub Actions for scheduled collection, validation, build, and deployment.
- GitHub Pages for hosting the static frontend.

There must be no required continuously running backend, server-side application on GitHub Pages, or browser-side hh.ru credentials.

Use maintained dependencies and lockfiles. Inspect the existing repository before choosing versions or restructuring files.

Suggested structure:

- `collector/`
- `analytics/`
- `config/`
- `schemas/`
- `tests/`
- `web/`
- `docs/`
- `.github/workflows/`

Adjust this structure when the repository already has suitable conventions.

## 3. Data access and hh.ru integration

Use the official hh.ru API as the primary source.

Before implementation, verify the current API documentation, authentication requirements, supported fields, search syntax, pagination rules, usage restrictions, and permitted data redistribution.

Do not assume anonymous access will work reliably.

Requirements:

- Configurable application identity and developer contact header.
- Credentials supplied through environment variables and GitHub Actions Secrets.
- Document the supported token setup and expiration behavior.
- Never expose tokens in frontend assets, exports, logs, repository history, or URLs.
- Bounded concurrency, configurable request budgets, timeouts, and retry policies.
- Respect rate limits and Retry-After where supplied.
- Backoff with jitter for transient failures.
- Treat authentication and CAPTCHA challenges as actionable collection failures.
- Do not implement CAPTCHA bypass, proxy rotation, or browser fingerprint evasion.
- Fetch full vacancy details when necessary for reliable extraction.
- Cache details and refresh them according to a configurable TTL.
- Load supported dictionary values from the API rather than inventing enum values.
- Handle missing fields, inaccessible vacancies, and schema evolution.

Respect the documented pagination ceiling. If a query exceeds the retrievable result limit, split it into supported narrower partitions, preferably publication windows and then other suitable dimensions. Deduplicate overlapping results.

Record unresolved truncation explicitly. Never label a truncated collection as complete.

Check redistribution requirements before publishing data. Prefer normalized facts, aggregate analytics, short evidence snippets, and source links where appropriate. Do not assume full vacancy descriptions may be republished publicly.

## 4. Discovery strategy

Discover both direct MLOps roles and adjacent infrastructure roles.

Direct search terms and aliases should include:

- MLOps / ML Ops / ML-Ops
- MLOps Engineer
- ML Platform Engineer
- ML Infrastructure Engineer
- AI Infrastructure Engineer
- AI Platform Engineer
- LLMOps
- ML SRE
- GPU Infrastructure Engineer
- Russian equivalents and common spelling variations

Adjacent discovery should include DevOps, SRE, Platform Engineer, Infrastructure Engineer, Kubernetes Engineer, and relevant Data Platform roles combined with meaningful ML signals.

Example signals:

- MLflow, ClearML, Kubeflow
- KServe, Seldon, BentoML
- Triton Inference Server, vLLM, TensorRT
- Ray, Ray Serve, KubeRay
- GPU clusters, CUDA, NVIDIA device plugin, GPU Operator, DCGM
- Model serving, inference, distributed training
- Feature stores, model registries, ML pipelines
- PyTorch or TensorFlow infrastructure
- LLM serving and AI platform operations

A generic DevOps vacancy mentioning Python or Kubernetes alone must not automatically become an MLOps vacancy.

Keep search definitions configurable. Record which searches discovered each vacancy.

Deduplicate by hh.ru vacancy ID. Detect likely reposts or near duplicates separately without silently merging distinct source IDs.

## 5. Relevance classification

Implement an explainable rules-based classifier first.

Suggested categories:

1. Core MLOps.
2. ML/AI platform and infrastructure.
3. DevOps/SRE with substantial ML responsibilities.
4. Data infrastructure adjacent to ML.
5. Weak or ambiguous ML relevance.
6. Irrelevant.

Provide:

- A relevance score from 0 to 100.
- A versioned scoring policy.
- Human-readable classification reasons.
- Evidence snippets from the source.
- Positive and negative signals.
- Separate title, responsibilities, requirements, and optional-skills signals.

Explicit ML infrastructure responsibilities should outweigh a passing mention of AI in a company description.

Default results should prioritize categories 1–3. Users can include adjacent and ambiguous results.

Do not present a heuristic relevance score as a calibrated probability.

## 6. Technology extraction and vacancy summaries

Create a configurable technology taxonomy with alias normalization.

Cover at least:

Infrastructure:
- Linux, networking, Bash, Python, Go.
- Docker, Podman, Kubernetes, Helm.
- Terraform, OpenTofu, Ansible, Packer.
- Argo CD, Flux, GitLab CI, GitHub Actions, Jenkins.

Observability:
- Prometheus, Grafana, OpenTelemetry.
- Loki, Elasticsearch, OpenSearch.
- Alertmanager, VictoriaMetrics.

ML lifecycle:
- MLflow, ClearML, Kubeflow, DVC.
- Airflow, Prefect, Dagster.
- Feast and other feature stores.

Serving and inference:
- KServe, Seldon, BentoML.
- NVIDIA Triton Inference Server.
- vLLM, TensorRT, TensorRT-LLM.
- ONNX Runtime, TorchServe, Ray Serve.

GPU and training:
- CUDA, NCCL, cuDNN.
- GPU Operator, NVIDIA device plugin, DCGM.
- MIG, GPU sharing, RDMA, InfiniBand.
- PyTorch, TensorFlow, JAX.
- DeepSpeed, FSDP, distributed training.
- Slurm, Volcano, Kueue, KubeRay.

Data:
- PostgreSQL, ClickHouse, Redis.
- Kafka, RabbitMQ.
- Spark, Flink.
- S3-compatible storage, MinIO.
- Relevant vector databases.

Cloud and platforms:
- AWS, Azure, GCP.
- Yandex Cloud, VK Cloud, Cloud.ru.
- OpenStack, VMware.
- OpenShift, OpenShift AI, Deckhouse.

Use word boundaries, aliases, context, and disambiguation. For example, distinguish NVIDIA Triton Inference Server from the Triton programming language.

For each extracted technology, preserve:

- Canonical name and category.
- Original matched text.
- Source section.
- Evidence.
- Requirement type: required, preferred, mentioned, or unclear.

Generate concise Russian vacancy summaries:

- What you will build or operate.
- Core stack.
- Required experience.
- ML-specific responsibilities.
- Required versus optional skills.
- Work arrangement.
- Salary, if disclosed.
- Important uncertainties.

Use deterministic extraction and templates by default. An optional LLM enrichment adapter may be added, but it must not be required to run the product. It must preserve evidence, validate structured output, cache results, and never invent missing requirements.

## 7. Data model and history

Use explicit schemas and migrations where appropriate.

Preserve:

- Source ID and URL.
- Title and employer identity.
- Location and available work arrangement fields.
- Source publication and creation timestamps, where available.
- First observed and last observed timestamps.
- Last detail refresh.
- Source-provided experience requirements.
- Separately inferred seniority and explicit years-of-experience statements.
- Original salary fields, currency, gross/net flag, and payment period.
- Categories, relevance score, technologies, evidence, and summaries.
- Discovery queries.
- Content hashes and meaningful change events.
- Availability status and status evidence.
- Extraction/classifier versions.

Distinguish:

- New to MlPops.
- Published on hh.ru during a date window.
- Updated.
- Archived according to the source.
- Inaccessible.
- Not found in the latest search.
- Unknown.

A vacancy missing from one search must not automatically become closed or archived.

Record title, salary, stack, description, and work-arrangement changes when supported by observed data.

Maintain an event history suitable for daily analytics and historical reconstruction.

## 8. Filters

Implement combinable filters with clear semantics, useful defaults, reset controls, selected-filter chips, and a shareable URL.

Support at least:

Relevance and role:
- Role category.
- Relevance score range.
- Core MLOps only.
- Include DevOps/SRE with ML responsibilities.
- Include or exclude ambiguous matches.
- Title-only versus full-text matching.
- Include and exclude words.

Skills:
- Required technology tags.
- ANY / ALL matching.
- Excluded technologies.
- Technology categories.
- Required versus preferred versus merely mentioned.
- GPU-related roles.
- Inference versus training.
- LLM infrastructure.
- Kubernetes-based ML platforms.
- MLflow / ClearML / Kubeflow presets.

Experience:
- Source experience bucket.
- Explicitly stated years, when extracted.
- Inferred seniority with an uncertainty indicator.
- No-experience opportunities.
- Junior-friendly.
- Roles suitable for a DevOps-to-MLOps transition.
- Deep ML research or mathematics requirements.
- Degree or PhD requirement, if explicitly stated.

Compensation:
- Salary disclosed.
- Minimum and maximum.
- Currency.
- Gross / net / unknown.
- Payment period.
- Lower-bound-only and upper-bound-only offers.
- Salary increase or decrease observed.

Location and conditions:
- Country, region, city.
- Remote, hybrid, on-site, or unknown.
- Employment type and schedule.
- Part-time or project work.
- Relocation explicitly offered.
- Business travel.
- On-call or shift responsibilities.
- English requirement and level when explicitly stated.

Employer:
- Employer search.
- Include and exclude employers.
- Direct employer versus agency only when supported by evidence.
- New employers in the observed dataset.
- Employers with multiple relevant openings.

Freshness and lifecycle:
- Published within 24 hours, 3 days, 7 days, 30 days, or a custom range.
- First discovered during a selected period.
- Active, archived, inaccessible, or unknown.
- Updated since the previous observation.
- Salary or stack changed.
- Possible reposts.
- Hide already viewed or dismissed jobs.
- Bookmarked and application-status filters.

Personal fit:
- Minimum skills-match score.
- Maximum number of missing required skills.
- Matches my target salary.
- Matches my desired work arrangement.
- Uses my existing DevOps strengths.

Treat unknown values as unknown. Do not interpret missing remote, salary, language, or on-call data as negative evidence.

Sort by relevance, publication date, first discovery, salary with comparable units, skill match, or number of missing requirements.

## 9. Main interface

Build a polished dashboard with three desktop columns:

LEFT:
- Search and filters.
- Collapsible filter groups.
- Saved presets.
- Personal skill profile access.

CENTER:
- Market KPI cards.
- Vacancy list and optional table view.
- Sorting, result count, and active filters.
- Vacancy detail drawer or modal.
- Tabs for vacancies, trends, skills, employers, and methodology.

RIGHT:
A sticky market insights dashboard showing technologies mentioned in the currently filtered vacancies.

Include:

- Top technologies with count and percentage.
- Required versus preferred skill breakdown.
- Technology category breakdown.
- Experience distribution.
- Work arrangement distribution.
- Salary disclosure rate.
- Top employers.
- Emerging technologies when enough history exists.
- Frequently co-occurring technology pairs.
- Skills missing from my profile.

Use the label “Технологии в вакансиях”. Do not label this as resume analytics.

Clicking a technology should apply a filter. Provide an obvious filtered-versus-global context indicator.

On smaller screens, convert filters and insights into usable drawers or tabs.

Visual direction:
- Professional engineering dashboard.
- Purple accent color.
- Light and dark themes.
- Readable cards, restrained animation, clear hierarchy.
- Accessible charts, keyboard navigation, adequate contrast.
- Proper loading, empty, partial-data, stale-data, and error states.

## 10. Vacancy cards and details

Each card should show:

- Title, employer, location.
- Remote/hybrid/on-site or unknown.
- Salary with original currency and gross/net status.
- Source experience requirement.
- Inferred seniority when useful, clearly labeled.
- Relevance category and score.
- Main technology tags.
- Short practical summary.
- Publication date and first-discovered date.
- New, updated, or possible-repost badges.
- Skills-match indicator.
- Bookmark, viewed, and dismiss actions.
- Direct link to hh.ru.

Details should expose classification reasons, required versus preferred technologies, evidence, change history, uncertainties, and a clearly labeled personal skills gap.

Render source content safely. Sanitize any retained HTML.

## 11. Daily statistics and metric definitions

Use Europe/Moscow as the default reporting timezone. Store timestamps in UTC.

Implement and document separate metrics:

- Unique relevant vacancies currently observed as active.
- Unique vacancies first discovered today.
- Observed vacancies with source publication dates today.
- Vacancies updated today.
- Source-confirmed archived vacancies today.
- Newly observed employers.
- Remote share.
- Salary disclosure rate.
- Salary distributions among comparable disclosed offers.
- Technology prevalence.
- Changes over 7 and 30 days.

Do not use “new today” ambiguously. Explain whether a metric uses publication date or first observation.

The initial import is an initial inventory, not evidence that all imported jobs appeared that day.

Today is incomplete until the day ends. Show the last successful refresh and “as of” time.

Keep publication counts subject to observed API coverage. Do not claim comprehensive market totals.

For technology prevalence:

- Count each technology at most once per vacancy.
- Use unique vacancies as the denominator.
- Show the denominator and missing-detail coverage.
- Do not count repeated mentions as multiple vacancies.

For salaries:

- Preserve ranges and open-ended values.
- Separate gross/net/unknown and payment periods.
- Do not silently combine currencies or infer tax-adjusted salaries.
- If currency normalization is added, record the rate source and date.
- Always show sample size.
- Hide misleading summaries when samples are too small.

## 12. Forecasting

Implement a real but appropriately modest forecast of daily new relevant vacancies.

Forecast **new arrivals**, not tomorrow’s active inventory, unless a separate defensible inventory model is implemented.

Requirements:

- Next-day forecast and a 7-day outlook.
- Clearly separate historical observations and predictions.
- Return non-negative values.
- Display prediction intervals and the method used.
- Avoid false precision.
- Do not forecast individual job titles or employers.

Data handling:

- Train on completed, sufficiently covered days.
- Missing collection days are missing values, not zero.
- Exclude initial-inventory artifacts.
- Flag coverage changes and search-definition changes.
- Never generate fake historical data.
- Never compare a partial current day directly with a full previous day without an explicit qualification.

Models:

- Start with a recent-mean baseline.
- Add a weekday seasonal baseline when enough weeks exist.
- Evaluate a simple count or time-series model only when justified by data volume.
- Prefer the baseline when a more complex model does not improve validation.

Validation:

- Rolling-origin evaluation with no future leakage.
- Report MAE and a suitable additional metric such as WAPE, handling zero denominators.
- Compare all models on the same evaluation dates.
- Assess interval coverage when sufficient validation history exists.
- Document the minimum data required for each method.

Cold start:

- Display “Недостаточно истории для прогноза” when appropriate.
- Explain how many complete observations are available.
- Do not fill the forecast chart with invented numbers.

Forecasts may be generated for a documented set of sufficiently populated segments. Arbitrary frontend filters must not inherit a global forecast and present it as segment-specific. Disable unsupported forecasts with an explanation.

Add optional MLflow tracking for model experiments if useful, but keep it disabled by default and avoid requiring an MLflow server for normal operation.

## 13. Personal skill profile and job-search workflow

Provide a local personal profile:

- Technologies I know.
- Optional proficiency levels.
- Technologies I want to learn.
- Target roles and seniority.
- Salary preferences.
- Work arrangement and location preferences.

Store it in browser localStorage. Do not publish it with the dataset.

Implement an explainable fit score that prioritizes required skills over optional ones and handles sparse vacancy data.

Show:

- Existing skills matched.
- Missing required skills.
- Missing preferred skills.
- Why the vacancy might fit a DevOps-to-MLOps transition.
- A learning-priority list based on the number of additional vacancies each skill could help unlock.

Do not describe skill overlap as hiring probability.

Include:

- Bookmarks.
- Viewed and dismissed states.
- Personal application statuses: interested, applied, interview, offer, rejected.
- Local notes.
- Side-by-side comparison of up to three vacancies.
- Saved filter presets.
- Export/import of personal settings and tracking data.
- CSV export of the current filtered results, with spreadsheet formula injection protection.
- Shareable filter URLs that exclude private notes and personal data.

Clearly explain that local browser data does not automatically sync between devices.

## 14. Historical insights

Add useful views for:

- Daily arrivals and observed active inventory.
- Technology prevalence over time.
- Employer hiring activity.
- Experience distribution over time.
- Remote/hybrid/on-site share.
- Salary disclosure and comparable salary distributions.
- Technology co-occurrence.
- Changed vacancies.
- Potential reposts.
- DevOps-adjacent versus core MLOps opportunities.

Use historical snapshots or event reconstruction. Do not apply today’s vacancy attributes retroactively to all earlier dates.

Show sample sizes, coverage caveats, and comparable periods.

Avoid calling a technology “trending” based on a handful of mentions. Use minimum counts and show absolute changes alongside percentage changes.

## 15. Durable data and scheduled execution

Design persistence explicitly. GitHub Actions runners are ephemeral.

For the initial implementation, use a dedicated data branch or another documented durable repository-backed state mechanism suitable for the expected dataset.

Requirements:

- Persist normalized state and historical events between runs.
- Do not rely on Actions cache or expiring workflow artifacts as the only history store.
- Avoid committing a growing binary SQLite file on every run.
- Prefer deterministic, partitioned text exports or another justified compact strategy.
- Reconstruct SQLite from durable state when needed.
- Keep sensitive raw responses out of public state.
- Include schema versions, checksums where useful, retention policy, and migration handling.
- Serialize overlapping collectors and prevent lost updates.
- Make reruns idempotent.
- Preserve the last valid published dataset if collection or validation fails.
- Record failed runs without creating artificial zero-count days.
- Use an atomic publication strategy.

Suggested refresh cadence: four times per day at off-hour minutes, configurable. Document the schedule timezone and display reporting dates in Europe/Moscow.

Provide workflow_dispatch for manual refreshes and bounded backfills. Do not imply a backfill can recover complete historical market data that the API no longer exposes.

## 16. GitHub Actions and Pages deployment

Implement workflows for:

1. Pull request CI.
2. Scheduled collection and data validation.
3. Frontend build and GitHub Pages deployment.

They may share a workflow where this makes state flow and permissions simpler.

CI should include:

- Python linting and meaningful tests.
- TypeScript checks and linting.
- Frontend tests.
- Production build.
- Export-schema validation.

Deployment should use the official GitHub Pages workflow approach with:

- Configure Pages.
- Upload Pages artifact.
- Deploy Pages.
- Correct Pages and OIDC permissions.
- A github-pages environment.

Verify current supported action versions before using them.

Support both repository subpaths and custom-domain/root hosting. Use a routing strategy that works with direct links and refreshes on GitHub Pages.

Be explicit about workflow triggers: a data commit created using GITHUB_TOKEN must not be assumed to trigger a separate push-based deployment. Build from the newly validated data in the same run, explicitly pass artifacts, or use another documented reliable mechanism.

Separate credentialed collection from untrusted PR execution. Never expose collection credentials to fork pull requests or execute untrusted code with secrets.

Document scheduled-workflow limitations, including delays and automatic disabling where applicable. Always show real data freshness in the UI.

If repository access is available and the user has authorized changes, configure the deployment within that scope. Otherwise provide working workflow files and exact remaining setup instructions. Do not claim deployment succeeded without a successful deployment URL.

## 17. Reliability and observability

Generate a collection run report containing:

- Run ID and timestamps.
- Configuration and taxonomy versions.
- Queries and partitions attempted.
- Pages fetched.
- API request count.
- Unique IDs found.
- Details refreshed or unavailable.
- New, changed, and confirmed archived counts.
- Duplicate counts.
- Query truncation and partial failures.
- Coverage status.
- Export validation results.

Use explicit statuses: complete, partial, failed.

Define “complete” as complete relative to the configured searches and retrievable API windows, not the entire hh.ru market.

Show freshness, last successful collection, coverage status, and missing history in the frontend.

A failed refresh must not turn the market into zero vacancies.

## 18. Demo mode

Provide deterministic synthetic fixtures so the application can be developed and reviewed without credentials.

Demo mode must:

- Be clearly labeled.
- Use synthetic employers or unmistakably fictional records.
- Remain separate from production datasets.
- Never silently replace a failed real collection.
- Never feed production analytics or forecasts.

Provide a realistic range of edge cases, including missing salaries, ambiguous skills, DevOps roles with real ML responsibilities, weak AI mentions, and changed vacancies.

## 19. Tests and acceptance criteria

Write meaningful tests for:

- Alias normalization and technology disambiguation.
- Required versus preferred skill extraction.
- False positives from company-level AI descriptions.
- Adjacent DevOps/SRE classification.
- Pagination partitioning and coverage reporting.
- Overlapping search deduplication.
- Idempotent collection.
- Rate limits, authentication errors, and partial failures.
- Lifecycle handling without false archival.
- Initial import versus new-arrival metrics.
- Moscow date boundaries.
- Missing days versus actual zero observations.
- Salary comparability.
- Forecast cold starts and leakage prevention.
- Filter ANY/ALL semantics.
- Right-dashboard consistency with filtered results.
- Personal profile persistence.
- Repository-subpath loading and routing.

Use recorded or synthetic fixtures in CI rather than depending on live hh.ru availability.

Acceptance criteria:

- The app runs locally with documented commands.
- The real collector works when valid credentials and access are provided.
- An ML-related DevOps role can appear even without “MLOps” in its title.
- An unrelated DevOps role is not promoted based on generic Kubernetes/Python mentions.
- Every classification and extracted requirement can be explained.
- Filters and right-side analytics agree.
- Daily history survives separate workflow runs.
- Missing data is never disguised as zero.
- Forecasts remain unavailable until sufficient history exists.
- No secret appears in browser bundles or published data.
- The production build works under a GitHub Pages repository path.
- Failed collection preserves the previous valid site.
- Demo and real data cannot be accidentally mixed.

## 20. Delivery and execution

Start by inspecting the repository and checking current official documentation. Write a concise implementation plan, then implement it.

Work in complete vertical slices:

1. API client, schemas, and fixtures.
2. Durable state and incremental collection.
3. Extraction, classification, and summaries.
4. Search, filters, vacancy cards, and right-side insights.
5. Daily history and personal skills matching.
6. Forecasting with cold-start handling.
7. CI, Pages deployment, and verification.

Keep the implementation focused and maintainable. Do not introduce Kubernetes, Redis, Kafka, a persistent API server, or a large language model dependency without a concrete requirement.

Deliver:

- Working source code.
- Configurable searches, taxonomy, and scoring.
- Example environment file without credentials.
- Documented CLI commands.
- Durable-state and export schemas.
- Tests and verified build.
- GitHub Actions workflows.
- Setup and deployment instructions.
- Metric definitions and methodology.
- Forecast limitations and evaluation results when available.
- Screenshots or an equivalent visual verification of desktop and mobile layouts.

Finish with a concise report of what was implemented, what was verified, the actual deployment status, and any external setup still required.

Do not invent live vacancy statistics, model accuracy, API access, historical coverage, or deployment success.


## Mandatory update: Svelte stack and minimal design

These requirements override any conflicting frontend or visual requirements above.

### Frontend stack

- Use **Svelte + TypeScript + Vite**, replacing React entirely.
- Use Svelte components and idiomatic reactive state management.
- Choose charting and UI dependencies compatible with Svelte. Replace the previous Recharts suggestion.
- Prefer plain CSS with shared design tokens. Add Tailwind only if it materially simplifies implementation.
- Keep the Python collector, analytics pipeline, static JSON exports, GitHub Actions, and GitHub Pages architecture.
- Ensure routing, asset paths, and data loading work under a GitHub Pages repository subpath.
- Update all frontend tests, build commands, dependencies, and documentation accordingly.

### Design direction

Create a simple, restrained, functional interface for daily use by engineers. Prioritize readable vacancy lists, fast filtering, and clear statistics.

Avoid the stereotypical appearance of an AI-generated SaaS dashboard:

- No decorative gradients, glowing elements, glassmorphism, or blurred backgrounds.
- No oversized headings, marketing hero sections, or promotional slogans occupying dashboard space.
- No excessive rounded cards, pill-shaped controls, shadows, or nested containers.
- No decorative emoji, sparkle icons, AI assistant widgets, or unnecessary illustrations.
- No animations that distract from browsing and comparing vacancies.
- No arbitrary charts or KPI cards added just to fill space.

Use:

- Neutral backgrounds, clear text, subtle borders, and one restrained accent color.
- A consistent spacing scale and compact, comfortable information density.
- Simple typography with strong hierarchy and readable Russian text.
- Modest corner radii and minimal shadows.
- Standard, predictable controls with visible labels.
- Compact vacancy rows or restrained cards.
- Tables where they improve comparison.
- Clear hover, focus, selected, disabled, loading, and error states.
- Color only when it communicates selection, status, or a meaningful chart distinction.

Purple is optional and must remain a subtle accent rather than dominate the interface.

Preserve the desktop layout: filters on the left, vacancies in the center, and technology statistics on the right. Use subtle separators and alignment to organize these areas.

The right dashboard should primarily use compact horizontal bars, counts, percentages, and short lists. Keep labels and sample sizes visible. Avoid decorative gauges and crowded pie charts.

Use progressive disclosure for advanced filters. The initial screen should make searching and reading vacancies straightforward.

The result should feel like a carefully designed engineering tool: calm, practical, consistent, and easy to understand.


## Additional mandatory requirements: localization, stack relevance radar, and deployment

### 1. Complete Russian and English versions

Implement full interface localization:

- Support Russian (`ru`) and English (`en`).
- Provide a visible RU / EN switch.
- Default to Russian and persist the selected language.
- Localize navigation, filters, buttons, chart labels, tooltips, dates, empty states, errors, methodology, and forecast explanations.
- Keep all interface strings in structured translation dictionaries.
- Use locale-aware date and number formatting.
- Preserve language selection in shareable URLs.
- Keep original vacancy titles and source evidence unchanged. Clearly label any translated summaries.
- Generate deterministic vacancy summaries in both languages from the same extracted facts.
- Keep technology and product names in their canonical spelling.
- Provide both `README.md` in English and `README.ru.md` in Russian.
- Test translation-key parity and fallback behavior.

### 2. Technology stack relevance radar

Add a dedicated **“Актуальность стека” / “Stack Relevance”** view and a compact version in the right sidebar.

Its purpose is to show how frequently technologies appear in the observed vacancies, how demand changes, and how well the user's skills match that demand.

For each technology, show:

- Number and percentage of unique vacancies mentioning it.
- Required versus preferred mentions.
- Number of unique employers mentioning it.
- Mentions in core MLOps versus adjacent DevOps/SRE roles.
- Change in prevalence between comparable periods.
- Absolute vacancy counts alongside percentage changes.
- A historical sparkline when sufficient data exists.
- Sample size, coverage, and last update.
- Whether the technology is already in the user's skill profile.

Support 7-, 30-, and 90-day windows where history permits.

Classify technologies using documented, configurable rules:

- **Common:** consistently frequent in the selected market segment.
- **Growing:** increasing prevalence with sufficient observations.
- **Emerging:** relatively new in the observed history and gaining mentions.
- **Stable:** limited change across comparable periods.
- **Declining mentions:** decreasing observed prevalence.
- **Insufficient data:** too little evidence for a reliable assessment.

Do not describe a technology as obsolete merely because its vacancy mentions declined. Market demand is not the same as technical quality or universal usefulness.

Compare equivalent cohorts and completed periods. Account for collection gaps and changes in search coverage. Do not compare a partial current period with a complete previous period without explicit qualification.

Offer views by:
- Role category.
- Experience level.
- Location and work arrangement.
- Inference, training, GPU infrastructure, and ML platforms.
- Required skills only versus all mentions.

Prefer a ranked horizontal bar chart and a demand-versus-growth scatterplot. Treat “radar” as the product concept; do not force unrelated technologies onto a decorative spider chart.

If implementing a composite relevance score:
- Publish its formula and component values.
- Version the scoring policy.
- Distinguish current demand from demand growth.
- Handle missing history without invented values.
- Explain that the score measures observed hiring demand within MlPops coverage.

Add personal insights such as:
- “Your skills cover X of Y vacancies with extracted requirements.”
- “Learning this technology could improve your skill overlap with N additional vacancies.”
- “These technologies frequently appear alongside Kubernetes in MLOps roles.”

Make these calculations explainable. Do not present them as a probability of receiving an offer.

All radar labels, explanations, and insights must be available in Russian and English.

### 3. GitHub Pages deployment is a required deliverable

Deliver a working static production build and a complete GitHub Actions deployment workflow.

Requirements:

- Build the Svelte + TypeScript + Vite frontend.
- Publish through the official GitHub Pages Actions workflow.
- Support `https://<owner>.github.io/<repository>/`.
- Configure asset paths, JSON loading, and navigation for the repository base path.
- Ensure language switching and shareable filter links work after direct navigation and page refresh.
- Run collection on GitHub Actions; the browser must consume prepared static exports.
- Persist collection history between runs.
- Publish refreshed data and the frontend through a reliable workflow sequence.
- Preserve the last valid dataset if collection fails.
- Keep credentials exclusively in GitHub Actions Secrets.
- Include manual deployment and refresh triggers.
- Document the exact repository settings required to enable Pages.

When repository access and authorization are available, complete deployment and verify the resulting URL, assets, both languages, filters, and stack relevance view.

Otherwise, deliver deployment-ready files and identify the exact remaining setup steps. Report deployment as pending until a successful Pages deployment is verified.

These requirements extend the existing specification. Keep Svelte and the simple, restrained visual design mandatory.

## Mandatory Git workflow: merge into main through a Pull Request

Implement all changes on a dedicated feature branch, for example `feat/mlpops`. Do not commit or push directly to `main`.

After implementation:

1. Run the required tests, linting, type checks, and production build.
2. Commit the changes with clear commit messages.
3. Push the feature branch.
4. Open a Pull Request targeting `main` (the GitHub equivalent of a Merge Request).
5. Describe the implemented features, architecture, validation results, required secrets, and any remaining setup.
6. Return the Pull Request URL for review.

Keep the Pull Request open for review. Do not merge it automatically.

Run CI on the Pull Request. Deploy the production site to GitHub Pages only after the changes are merged into `main`. Scheduled collection must use the implementation from `main`.

If repository permissions prevent pushing or opening the Pull Request, preserve the completed work on the feature branch and report the exact blocker. Do not claim that a Pull Request was created unless its URL is available.

This rule overrides any earlier instruction that would publish the initial implementation before review and merge.