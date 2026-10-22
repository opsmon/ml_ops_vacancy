# Candidate verification

Implementation checked locally on 2026-10-22 (Europe/Moscow).

- Python: 35 offline tests pass; Ruff lint and formatting pass.
- Frontend: Svelte/TypeScript check reports zero errors/warnings; ESLint passes; 23 Vitest tests pass.
- Versioned Pydantic/JSON Schema export validates the 12-record synthetic fixture.
- Production Vite build works at `/ml_ops_vacancy/`; JavaScript is approximately 150 kB before compression.
- Playwright verifies desktop Chromium and Pixel 7 viewport with the built static preview: both languages, URL/filter persistence, sidebar denominator consistency, profiles/bookmarks/notes/application persistence, two-way comparison, cold-start forecast and HTTP failure behavior. Final browser results and artifact hashes are recorded in PR CI.
- Screenshots: [desktop RU](screenshots/desktop-vacancies-ru.png), [desktop EN](screenshots/desktop-vacancies-en.png), [mobile RU](screenshots/mobile-vacancies-ru.png), [mobile EN](screenshots/mobile-vacancies-en.png), [desktop stack](screenshots/desktop-stack-en.png), [mobile stack](screenshots/mobile-stack-en.png).

CI uploads `candidate-<commit>` containing the exact production artifact, screenshots, browser report and `build-evidence.json` with candidate SHA and per-file/tree SHA-256. Job summary repeats the artifact evidence. Generated local evidence is not tracked because it would point at the previous commit; CI generates evidence from the actual reviewed commit.

## Deployment and external prerequisites

GitHub Pages source is configured as `workflow`, public audience, HTTPS enabled. **Production is not deployed**: the requested PR must remain open for review, and initial publication is only allowed after merge into main. The returned Pages settings URL is not a successful deployment result.

No real hh.ru API collection was tested. Credentials and written permission to publish real data were not supplied. Synthetic fixture validation exercises API transport, error policies and state reconstruction without making live availability claims. No live statistics, historical coverage or forecast accuracy is asserted. Real publication remains blocked until access, redistribution permission and a successful collector run exist.

There is no running backend, migration service or ingress in this architecture. Candidate deployment verification uses the actual static production build in a fresh preview server at the intended repository path. Root/custom-domain build support is controlled by `BASE_PATH`; the primary browser suite intentionally tests the more error-prone repository subpath. Actual production URL/assets must be verified by the Pages workflow after review/merge.
