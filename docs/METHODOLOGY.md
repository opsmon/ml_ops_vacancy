# Methodology 1.0.0

## Observations and lifecycle

MlPops measures its configured searches, not all hh.ru vacancies or the entire labor market. Category defaults are 1–3: core MLOps, ML/AI platform infrastructure, and DevOps/SRE with operational ML responsibilities. Categories 4–6 allow adjacent data infrastructure, ambiguous mentions and irrelevant records to be inspected. Classification uses configurable weights and thresholds, title patterns, section evidence and operational ML signals. Generic Python/Kubernetes or a company describing itself as AI does not establish MLOps duties. Heuristic scores are not calibrated probabilities.

Each technology uses word-boundary aliases and retains its matched spelling, section, requirement type and a short source snippet. Explicit preferred-language markers override section defaults. NVIDIA Triton Inference Server requires an explicit inference/server alias; bare Triton does not identify it. Rule-based section parsing and summaries have uncertainty and must be checked against source links. Titles and evidence remain original. Deterministic RU/EN summaries use the same facts and do not imply translation of source evidence.

Source publication/creation and first/last observation are separate. Initial inventory events are excluded from arrival counts. Updates record changes to title, salary, technologies, description hash, work arrangement and source status. A missing search result is not an archive event; a 404/410 is inaccessible. Archived status requires source evidence. Possible reposts keep distinct source IDs and only flag matching normalized title+employer groups.

## Daily metrics

Store UTC; report Europe/Moscow. Daily arrivals count unique category 1–3 IDs with a non-inventory `discovered` event on that day. Publication counts use the source publication date among observed IDs; updates and confirmed archives count unique event IDs. Employer discovery excludes initial inventory. Active inventory is the last successful observed snapshot, not a market-wide stock estimate. Remote share, salary disclosure and technology prevalence use unique vacancies in the stated cohort, including unknowns in the denominator and showing detail coverage.

A usable training/comparison day is completed, has at least two successful non-initial runs spanning 12 hours, has unchanged search/taxonomy/scoring signature, has no failed/partial runs and contains no initial import. Missing days are null. Current days remain incomplete. Coverage gaps and config changes invalidate comparable windows. A day with a documented zero arrivals is valid only after its coverage criteria are met.

Technology prevalence counts a technology at most once per vacancy and excludes company-only mentions. Required and preferred counts can both include the same vacancy when separate evidence supports each. Salary comparisons retain original currency, gross/net/unknown, payment period and granularity. No FX/tax conversion. Closed-range midpoints are used for medians only within comparable units, at least five records and known period; open ranges stay open and are not imputed.

## Personal fit

For unique explicit required and preferred skills (preferred excludes already-required names):

`overlap = 100 × (3 × matched_required + matched_preferred) / (3 × total_required + total_preferred)`

No extracted requirements gives unknown, not perfect fit. Missing required/preferred sets and matched skills are visible. Proficiency levels and target roles are stored preferences, not unsupported claims of qualification. Transition suggestions require an ML-relevant role and extracted infrastructure requirements. Learning priorities show the number of vacancies with a missing required skill, plus the subset for which that skill is the sole missing requirement. These are explainable overlap measures, not offer probabilities.

## Stack relevance

Current counts, percentages, unique employers, core-vs-adjacent counts and required/preferred mentions come from the filtered vacancies. A 7/30/90-day assessment requires **both** immediately preceding completed periods, identical signatures, a snapshot for every covered day and supported historical cohort fields (category, experience, location, work arrangement, ML responsibility flags, requirement type). Text, lifecycle changes and personal filters unsupported by snapshots disable assessment. Daily last snapshots are deduplicated by source ID within each period; a repeated vacancy is not a new mention each day. History uses original snapshot attributes rather than today's attributes.

Configurable defaults: minimum 20 vacancies per period, five technology mentions and three employers in each period; changes of at least +5 percentage points are growing and at most −5 are declining mentions. Common is at least 35% in both periods after growth/decline checks. Stable changes are within 3 points. Intermediate weak evidence remains insufficient. Emerging requires a first observed technology in the recent period plus enough current observations and at least 5 points of growth. The initial history boundary cannot demonstrate novelty outside MlPops coverage. Absolute counts and denominators accompany percentage changes. No composite score is used. Declining mentions do not mean a technology is obsolete.

Public removal of archived details reduces historical per-vacancy reconstruction; aggregate daily inventory remains as originally observed. Public reconstructed cohorts therefore describe retained observable records, with sample size always visible, and may differ from original aggregate counts. Do not interpret that as a complete retrospective inventory.

## Forecasts

Only category 1–3 **new arrivals** are forecast, not total active inventory. At least 14 eligible completed days are required; the latest must be within two days and the last 14 span at most 20 days. Initial-import artifacts, missing/partial/current/future days and different search signatures are excluded. Cold starts have no forecast points.

Recent-mean baseline: up to 28 eligible observations. Weekday baseline: up to 56 observations, considered only with at least 56 complete days and at least four prior samples per weekday before evaluation. Rolling-origin validation trains only on earlier dates. All candidates use identical evaluation dates. Select weekday only with at least 5% lower MAE; otherwise retain recent mean. WAPE is total absolute error / total actual arrivals and is null for a zero denominator.

Seven future daily point estimates are rounded and non-negative. Nominal 80% intervals use the empirical 80th percentile of absolute rolling errors, clipped to non-negative counts. Interval validation uses only earlier residuals; observed coverage appears after 14 such assessments. These are modest, uncalibrated empirical intervals, not guaranteed coverage. No ARIMA, LLM or MLflow server is required. Arbitrary frontend filters never inherit global predictions. No real forecast evaluation results exist until sufficient actual coverage accumulates.
