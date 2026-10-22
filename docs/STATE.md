# Durable state and migrations

Each run reconstructs a SQLite working index (`PRAGMA user_version=1`) with vacancy and event tables from the checksummed text state. The index is ephemeral and disposable. SQLite files, raw API responses and secrets are never committed. The authoritative text layout is:

```text
manifest.json                  schema version, mode, SHA-256 checksums
vacancies/<source-id>.json     normalized facts and per-ID events
runs/<run-id>.json             complete/partial/failed reports
snapshots/<run-id>.json        immutable cohort attributes at successful observations
dictionaries.json             source enum values and area lookup
```

Hashes use canonical sorted-key JSON, UTF-8, preserving Unicode. Export schema is generated from Pydantic models; `schemas/export-v1.json` is checked against it in CI. Manifest schema is in `schemas/state-v1.json`. A schema or mode mismatch fails closed; migration requires a new version, an explicit offline conversion and tests. Keep the old data-branch commit as rollback before applying a migration. No migration from an earlier schema exists because v1 is the first version.

Local saving writes a sibling staging directory and swaps it into place. A previous directory is retained during the replacement and restored if replacement fails. On GitHub, a single `data` branch commit is the atomic durable publication boundary. The publication workflow uses one shared concurrency group with cancellation disabled for collection and publishing, and a fresh data worktree. Its normal fast-forward push refuses lost-update races. Do not operate a second unmanaged writer against this branch.

Failed/partial runs roll back vacancy mutations and do not append successful snapshots. Their run reports survive independently, without overwriting the previous public JSON. Failed days are not zero-arrival days. Export validation must succeed before publishing. Complete is relative to configured retrievable searches, never the entire hh.ru market. Details inaccessible with source 404/410 are an observed unknown, not a collection transport failure or proof of archival.

Rerunning a run ID is idempotent. Different run IDs can refresh observations but do not append duplicate changes when tracked facts are equal. Source IDs are never merged; exact normalized title+employer groups flag possible reposts. A missing search ID only changes `found_latest`; detail refresh determines source availability.

## Retention and size

The v1 policy retains normalized per-ID facts and events for the life of the dataset and successful snapshots/run reports for one year. Public exports include the last 100 reports and one year of daily/snapshot history. No automatic history rewriting or destructive git compaction is performed. Archived public vacancy facts are removed under the public-export gate. Back up the branch before any operator-approved purge; git history itself retains old commits and is **not an erasure mechanism**.

This repository-backed design targets a narrow MLOps segment. Snapshot growth is linear in observed vacancies × runs; monitor repository and Pages artifact size. Larger datasets should move to permission-compatible private object storage before repository size becomes material. Never substitute an expiring Actions artifact/cache for the durable state branch.
