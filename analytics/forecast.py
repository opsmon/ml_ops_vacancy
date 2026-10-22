"""Conservative recent-mean/weekday baselines with rolling-origin comparison."""

import math
from datetime import datetime, timedelta
from statistics import mean


def weekday(day):
    return datetime.fromisoformat(day).weekday()


def predict(train, date, method):
    values = [r["arrivals"] for r in train[-28:]]
    if method == "weekday":
        values = [r["arrivals"] for r in train[-56:] if weekday(r["date"]) == weekday(date)]
    return max(0, mean(values))


def forecast(rows, today):
    today = today[:10]
    rows = sorted([r for r in rows if r["date"] <= today], key=lambda r: r["date"])
    # Restrict to the latest signature, completed past dates, never use current/future values.
    eligible = [r for r in rows if r.get("complete") and r.get("arrivals") is not None and r["date"] < today]
    signature = rows[-1].get("config_hash") if rows else None
    eligible = [r for r in eligible if r.get("config_hash") == signature]
    result = {
        "status": "insufficient",
        "observations": len(eligible),
        "minimum": 14,
        "method": None,
        "evaluation": {},
        "predictions": [],
        "segment": "categories_1_3",
    }
    # Recent coverage only; sparse scattered history cannot support next-day claims.
    if (
        len(eligible) < 14
        or (datetime.fromisoformat(today) - datetime.fromisoformat(eligible[-1]["date"])).days > 2
    ):
        return result
    recent_days = (
        datetime.fromisoformat(eligible[-1]["date"]) - datetime.fromisoformat(eligible[-14]["date"])
    ).days
    if recent_days > 20:
        return result
    methods = ["recent_mean"]
    if len(eligible) >= 56 and all(
        sum(weekday(r["date"]) == d for r in eligible[:-7]) >= 4 for d in range(7)
    ):
        methods.append("weekday")
    start = 28 if "weekday" in methods else 7
    errors = {m: [] for m in methods}
    actuals = []
    # Every candidate evaluated on the identical dates using only earlier observations.
    for index in range(start, len(eligible)):
        row = eligible[index]
        actuals.append(row["arrivals"])
        for method in methods:
            errors[method].append(abs(row["arrivals"] - predict(eligible[:index], row["date"], method)))
    evaluation = {}
    for method, values in errors.items():
        evaluation[method] = {
            "mae": round(mean(values), 2),
            "wape": round(sum(values) / sum(actuals), 3) if sum(actuals) else None,
            "n": len(values),
            "dates": [r["date"] for r in eligible[start:]],
        }
    chosen = min(methods, key=lambda m: evaluation[m]["mae"])
    if chosen != "recent_mean" and evaluation[chosen]["mae"] >= evaluation["recent_mean"]["mae"] * 0.95:
        chosen = "recent_mean"
    residuals = sorted(errors[chosen])
    # Nominal 80% empirical absolute-error interval; assessment uses prior residuals only.
    radius = residuals[min(len(residuals) - 1, math.ceil(0.8 * len(residuals)) - 1)]
    intervals = []
    for index in range(10, len(errors[chosen])):
        prior = sorted(errors[chosen][:index])
        q = prior[min(len(prior) - 1, math.ceil(0.8 * len(prior)) - 1)]
        intervals.append(errors[chosen][index] <= q)
    result.update(
        status="available",
        method=chosen,
        evaluation=evaluation,
        interval={
            "nominal": 0.8,
            "method": "empirical_absolute_error",
            "coverage": mean(intervals) if len(intervals) >= 14 else None,
            "validation_n": len(intervals),
        },
    )
    for offset in range(1, 8):
        date = (datetime.fromisoformat(today) + timedelta(days=offset)).date().isoformat()
        value = predict(eligible, date, chosen)
        result["predictions"].append(
            {
                "date": date,
                "value": round(value),
                "lower": max(0, math.floor(value - radius)),
                "upper": math.ceil(value + radius),
            }
        )
    return result
