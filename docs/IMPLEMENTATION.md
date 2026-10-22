# Implementation plan

1. Verify hh.ru API/terms and GitHub action versions. Establish versioned contracts and fictional fixtures.
2. Implement an authenticated, bounded API client, five-minute partitioning, SQLite reconstruction, incremental events and atomic text state.
3. Add configurable extraction, evidence, classification, bilingual summaries and lifecycle handling.
4. Build a compact Svelte RU/EN workspace: composable URL filters, vacancy details/comparison, filtered insights and local personal workflow.
5. Add Moscow daily metrics, historical snapshots, conservative forecasts and comparable-period stack assessments.
6. Exercise offline pipeline/UI tests and repository-subpath preview; record screenshots and checksums.
7. Push one feature branch and open one PR. Keep it open. Pages only deploys from main after review.

Public real-data publication is gated on explicit hh.ru permission: current terms sections 3.11, 4.3 and 4.6 restrict archival display and redistribution. Demo is an explicit independent mode, never a failure fallback. No live access or history is assumed.
