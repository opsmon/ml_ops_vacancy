"""Search partitioning, incremental refresh and transactional validated publication."""

import json
import math
import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from analytics.forecast import forecast
from analytics.metrics import calendar_series, daily_metrics, snapshot
from collector.api import AccessFailure, CollectionError, HHClient, Unavailable
from collector.extract import ROOT, TAXONOMY, digest, normalize
from collector.models import Dataset, RunReport
from collector.state import State


def stamp(dt):
    return dt.astimezone(UTC).isoformat(timespec="seconds")


def search(client, query, start, end, report, minimum_minutes=5):
    """Inclusive overlapping five-minute boundaries prevent gaps after API rounding."""
    params = {
        "text": query["text"],
        "per_page": 100,
        "page": 0,
        "date_from": stamp(start),
        "date_to": stamp(end),
    }
    params.update(query.get("params", {}))
    result = client.get("/vacancies", params)
    report.pages += 1
    report.partitions.append(
        {"query": query["id"], "from": stamp(start), "to": stamp(end), "found": result.get("found", 0)}
    )
    if result.get("found", 0) > 2000:
        if end - start > timedelta(minutes=minimum_minutes):
            seconds = int((end - start).total_seconds() / 2)
            seconds = max(300, seconds // 300 * 300)
            middle = start + timedelta(seconds=seconds)
            yield from search(client, query, start, middle, report, minimum_minutes)
            yield from search(client, query, middle, end, report, minimum_minutes)
            return
        report.truncations.append(report.partitions[-1])
    yield from result.get("items", [])
    pages = min(20, result.get("pages", math.ceil(min(2000, result.get("found", 0)) / 100)))
    for page in range(1, pages):
        params["page"] = page
        result = client.get("/vacancies", params)
        report.pages += 1
        yield from result.get("items", [])


def config_hash(config):
    return digest(
        {
            "searches": config,
            "taxonomy": TAXONOMY,
            "scoring": json.loads((ROOT / "config/scoring.json").read_text()),
        }
    )


def collect(state, client, config, now, days=None):
    config = {**config, "lookback_days": min(90, max(1, days or config["lookback_days"]))}
    initial = not state.vacancies
    now_s = stamp(now)
    run = RunReport(
        id=now.strftime("%Y%m%dT%H%M%SZ"),
        started_at=now_s,
        finished_at=now_s,
        status="complete",
        initial_inventory=initial,
        config_hash=config_hash(config),
        taxonomy_version=TAXONOMY["version"],
    )
    # Idempotent rerun of the same run ID.
    if any(r.id == run.id for r in state.runs):
        return next(r for r in state.runs if r.id == run.id)
    lookback = min(90, max(1, days or config["lookback_days"]))
    end = now.replace(second=0, microsecond=0) + timedelta(minutes=5 - now.minute % 5)
    start = (now - timedelta(days=lookback)).replace(second=0, microsecond=0)
    start -= timedelta(minutes=start.minute % 5)
    items, discoveries = {}, {}
    before = {k: v.model_copy(deep=True) for k, v in state.vacancies.items()}
    try:
        area_context = state.dictionaries.get("_area_context")
        state.dictionaries = client.get("/dictionaries")
        if area_context is None:
            area_context = {}

            def visit(area, country, region=None):
                area_context[str(area["id"])] = {"country": country, "region": region}
                for child in area.get("areas", []):
                    visit(child, country, region or child["name"])

            for country in client.get("/areas"):
                visit(country, country["name"])
        state.dictionaries["_area_context"] = area_context
        # Validate configurable dictionary-backed filters; unknown parameters must not be silently ignored.
        supported = {
            "area": None,
            "experience": "experience",
            "search_field": "vacancy_search_fields",
            "work_format": "work_format",
            "employment_form": "employment_form",
        }
        for query in config["queries"]:
            for key, value in query.get("params", {}).items():
                if key not in supported:
                    raise CollectionError("Unsupported search parameter in configuration")
                dictionary = supported[key]
                values = value if isinstance(value, list) else [value]
                if dictionary and not all(
                    v in {x["id"] for x in state.dictionaries.get(dictionary, [])} for v in values
                ):
                    raise CollectionError("Unknown dictionary filter value")
                if key == "area" and not all(str(v) in area_context for v in values):
                    raise CollectionError("Unknown source area filter")
            run.queries.append(query["id"])
            try:
                for item in search(client, query, start, end, run, config.get("min_partition_minutes", 5)):
                    source_id = str(item["id"])
                    if source_id in items:
                        run.duplicates += 1
                    items[source_id] = item
                    discoveries.setdefault(source_id, set()).add(query["id"])
            except AccessFailure:
                raise
            except (CollectionError, KeyError, TypeError):
                run.failures.append("Search failed: " + query["id"])
                break
        run.unique_ids = len(items)
        ttl = timedelta(hours=float(os.getenv("HH_DETAIL_TTL_HOURS", "24")))
        # Refresh previously observed IDs too: search omission never implies archival.
        for source_id in sorted(set(items) | set(state.vacancies)):
            old = state.vacancies.get(source_id)
            discovered = source_id in items
            if old and old.detail_refreshed and now - datetime.fromisoformat(old.detail_refreshed) < ttl:
                old.found_latest = discovered
                if discovered:
                    old.last_seen = now_s
                    old.queries = sorted(set(old.queries) | discoveries.get(source_id, set()))
                continue
            try:
                raw = client.get(f"/vacancies/{source_id}")
                raw["_area_context"] = area_context.get(str((raw.get("area") or {}).get("id")), {})
                vacancy = normalize(raw, now_s, discoveries.get(source_id, set()))
                vacancy.found_latest = discovered
                if not discovered and old:
                    vacancy.last_seen = old.last_seen
                outcome = state.observe(vacancy, now_s, initial)
                run.details_refreshed += 1
                run.new += outcome == "new"
                run.changed += outcome == "changed"
                run.archived += vacancy.status == "archived" and (old is None or old.status != "archived")
            except Unavailable:
                run.details_unavailable += 1
                if old:
                    vacancy = old.model_copy(deep=True)
                    vacancy.status = "inaccessible"
                    vacancy.status_evidence = "source_404_or_410_not_archival"
                    vacancy.detail_refreshed = now_s
                    vacancy.found_latest = discovered
                    state.observe(vacancy, now_s)
                else:
                    # Search metadata without details remains explicitly unknown.
                    vacancy = normalize(items[source_id], now_s, discoveries.get(source_id, set()))
                    vacancy.status, vacancy.status_evidence = "inaccessible", "detail_unavailable"
                    state.observe(vacancy, now_s, initial)
            except AccessFailure:
                raise
            except (CollectionError, ValueError, KeyError, TypeError):
                run.failures.append("Detail refresh failed")
                break
        if run.failures or run.truncations:
            run.status = "partial"
    except AccessFailure:
        run.status = "failed"
        run.failures.append("Authentication or CAPTCHA failure; review application access")
    except (CollectionError, ValueError, KeyError, TypeError):
        run.status = "failed"
        run.failures.append("Collection failed; review configuration, dictionaries and API availability")
    run.requests = client.count
    run.finished_at = stamp(
        now
    )  # Injected clock keeps deterministic fixtures; CLI updates real finish below.
    if run.status != "complete":
        # Roll back all vacancy mutations. Preserve failed reports without false zero snapshots.
        state.vacancies = before
        state.db.execute("DELETE FROM vacancies")
        state.db.execute("DELETE FROM events")
        for vacancy in before.values():
            state.index(vacancy)
    else:
        state.reposts()
        state.snapshots.append(snapshot(state, run))
    state.runs.append(run)
    return run


def export(state, now, public=False):
    if state.mode == "real" and public and not os.getenv("HH_PUBLICATION_PERMISSION"):
        raise PermissionError("Public hh.ru data export needs documented written permission; see docs/API.md")
    rows = calendar_series(daily_metrics(state, now))
    successes = [r for r in state.runs if r.status == "complete"]
    latest = state.runs[-1] if state.runs else None
    # Source-confirmed archival is excluded from public real data, including per-vacancy historical facts.
    vacancies = list(state.vacancies.values())
    snapshots = state.snapshots
    if state.mode == "real" and public:
        allowed = {v.id for v in vacancies if v.status == "active"}
        vacancies = [v for v in vacancies if v.id in allowed]
        snapshots = [{**s, "vacancies": [v for v in s["vacancies"] if v["id"] in allowed]} for s in snapshots]
    return Dataset(
        mode=state.mode,
        generated_at=now,
        last_success=successes[-1].finished_at if successes else None,
        coverage=latest.status if latest else "none",
        config_hash=latest.config_hash if latest else "none",
        vacancies=vacancies,
        runs=state.runs[-100:],
        daily=rows,
        snapshots=snapshots,
        forecast=forecast(rows, now),
        taxonomy=TAXONOMY["technologies"],
        dictionaries={k: v for k, v in state.dictionaries.items() if not k.startswith("_")},
    )


def write_export(dataset, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dataset.model_dump_json(indent=2)
    Dataset.model_validate_json(payload)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as file:
        file.write(payload + "\n")
        temporary = file.name
    os.replace(temporary, path)


def run_real(state_path, output, days=30, public=False):
    state = State(state_path, "real")
    try:
        if public and not os.getenv("HH_PUBLICATION_PERMISSION"):
            raise AccessFailure("Public data publication permission missing")
        client = HHClient()
    except AccessFailure:
        now = datetime.now(UTC)
        report = RunReport(
            id=now.strftime("%Y%m%dT%H%M%SZ"),
            started_at=stamp(now),
            finished_at=stamp(now),
            status="failed",
            initial_inventory=not state.vacancies,
            config_hash=config_hash(json.loads((ROOT / "config/searches.json").read_text())),
            taxonomy_version=TAXONOMY["version"],
            failures=[
                "Configure HH_TOKEN, a real HH_USER_AGENT contact and public-export permission when required"
            ],
        )
        state.runs.append(report)
        state.save()
        print(report.model_dump_json())
        return 1
    try:
        report = collect(
            state, client, json.loads((ROOT / "config/searches.json").read_text()), datetime.now(UTC), days
        )
    finally:
        client.close()
    report.finished_at = stamp(datetime.now(UTC))
    if report.status == "complete":
        state.snapshots[-1] = snapshot(state, report)
        report.export_validated = True
        data = export(state, report.finished_at, public=public)
        state.save()
        write_export(data, output)
    else:
        state.save()
    print(json.dumps(report.model_dump(), ensure_ascii=False))
    return 0 if report.status == "complete" else 1
