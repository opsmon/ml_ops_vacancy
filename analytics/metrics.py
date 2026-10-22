"""All timestamps UTC; all reporting dates Europe/Moscow. No synthetic history."""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

MSK = ZoneInfo("Europe/Moscow")


def local_day(timestamp):
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(MSK).date().isoformat()


def relevant(vacancies):
    return [v for v in vacancies if v.category <= 3]


def snapshot(state, run):
    vacancies = relevant(list(state.vacancies.values()))
    active = [v for v in vacancies if v.status == "active"]
    return {
        "id": run.id,
        "at": run.finished_at,
        "day": local_day(run.finished_at),
        "config_hash": run.config_hash,
        "initial": run.initial_inventory,
        "coverage": run.status,
        # Immutable historical attributes, used for equivalent cohort comparisons.
        "vacancies": [
            {
                "id": v.id,
                "employer_id": v.employer_id,
                "category": v.category,
                "experience": v.experience,
                "location": v.location,
                "arrangement": v.arrangement,
                "flags": v.flags,
                "salary": v.salary.model_dump() if v.salary else None,
                "technologies": [t.model_dump() for t in v.technologies],
                "detail": "details_missing" not in v.uncertainties,
            }
            for v in active
        ],
        "active": len(active),
    }


def daily_metrics(state, now):
    today = local_day(now)
    runs_by_day = defaultdict(list)
    for run in state.runs:
        runs_by_day[local_day(run.finished_at)].append(run)
    snapshots = {s["id"]: s for s in state.snapshots}
    rows = []
    for day, runs in sorted(runs_by_day.items()):
        complete = sorted([r for r in runs if r.status == "complete"], key=lambda r: r.finished_at)
        noninitial = [r for r in complete if not r.initial_inventory]
        span = (
            (
                datetime.fromisoformat(complete[-1].finished_at)
                - datetime.fromisoformat(complete[0].finished_at)
            ).total_seconds()
            if complete
            else 0
        )
        signature = {r.config_hash for r in runs}
        covered = (
            day < today
            and len(noninitial) >= 2
            and span >= 12 * 3600
            and len(signature) == 1
            and all(r.status == "complete" for r in runs)
            and not any(r.initial_inventory for r in runs)
        )
        snap = snapshots.get(complete[-1].id) if complete else None
        # Historical relevance belongs to the event, never to today's reclassified record.
        observed = [
            (v.id, e) for v in state.vacancies.values() for e in v.events if e.after.get("category", 6) <= 3
        ]
        arrivals = {
            source_id for source_id, e in observed if e.kind == "discovered" and local_day(e.at) == day
        }
        updated = {source_id for source_id, e in observed if e.kind == "updated" and local_day(e.at) == day}
        archived = {
            source_id
            for source_id, e in observed
            if "status" in e.fields and e.after.get("status") == "archived" and local_day(e.at) == day
        }
        published = {
            source_id
            for source_id, e in observed
            if e.after.get("published_at")
            and local_day(e.after["published_at"]) == day
            and local_day(e.at) <= day
        }
        employer_first = {}
        for _, e in sorted(observed, key=lambda item: item[1].at):
            employer_first.setdefault(e.after.get("employer_id"), e)
        new_employers = sum(
            local_day(e.at) == day and e.kind == "discovered" for e in employer_first.values()
        )
        rows.append(
            {
                "date": day,
                "complete": covered,
                "partial_today": day == today,
                "config_hash": next(iter(signature)) if len(signature) == 1 else "changed",
                "initial_inventory": any(r.initial_inventory for r in runs),
                "arrivals": len(arrivals) if noninitial else None,
                "published": len(published) if complete else None,
                "updated": len(updated) if complete else None,
                "archived": len(archived) if complete else None,
                "new_employers": new_employers if noninitial else None,
                "active": snap["active"] if snap else None,
                "successful_runs": len(complete),
                "coverage_hours": round(span / 3600, 1),
            }
        )
    return rows


def salary_groups(vacancies, minimum=5):
    groups = defaultdict(list)
    for v in vacancies:
        if not v.salary:
            continue
        s = v.salary
        # No cross-currency/tax/period merging and no fabricated midpoint for open ranges.
        if s.lower is not None and s.upper is not None:
            groups[(s.currency, s.gross, s.period, s.mode)].append((s.lower + s.upper) / 2)
    result = []
    for key, values in groups.items():
        values.sort()
        n = len(values)
        result.append(
            {
                "currency": key[0],
                "gross": key[1],
                "period": key[2],
                "mode": key[3],
                "n": n,
                "median": (values[(n - 1) // 2] + values[n // 2]) / 2
                if n >= minimum
                and key[0]
                and key[1] is not None
                and key[2] != "unknown"
                and key[3] != "unknown"
                else None,
            }
        )
    return result


def prevalence(vacancies):
    counter = Counter()
    for v in vacancies:
        counter.update({t.name for t in v.technologies if t.section != "company"})
    return {
        name: {"count": count, "percent": round(100 * count / len(vacancies), 1)}
        for name, count in counter.items()
    }


def calendar_series(rows):
    if not rows:
        return []
    by_day = {r["date"]: r for r in rows}
    start, end = datetime.fromisoformat(rows[0]["date"]), datetime.fromisoformat(rows[-1]["date"])
    result = []
    while start <= end:
        day = start.date().isoformat()
        result.append(by_day.get(day, {"date": day, "complete": False, "arrivals": None, "active": None}))
        start += timedelta(days=1)
    return result
