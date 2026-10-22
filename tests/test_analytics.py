from datetime import UTC, datetime, timedelta

from analytics.forecast import forecast
from analytics.metrics import calendar_series, daily_metrics, local_day, prevalence, salary_groups
from collector.demo import DEMO_TIME, raw_fixture
from collector.extract import normalize
from collector.pipeline import collect
from collector.state import State
from tests.test_pipeline import CONFIG, Fake


def test_moscow_midnight_and_initial_inventory(tmp_path):
    assert local_day("2026-10-21T21:00:00+00:00") == "2026-10-22"
    assert local_day("2026-10-21T20:59:59+00:00") == "2026-10-21"
    state = State(tmp_path / "s", "real")
    collect(state, Fake(), CONFIG, datetime.fromisoformat(DEMO_TIME))
    rows = daily_metrics(state, "2026-10-23T12:00:00+00:00")
    assert rows[0]["arrivals"] is None and not rows[0]["complete"]


def test_zero_arrivals_requires_real_complete_day(tmp_path):
    state = State(tmp_path / "s", "real")
    for stamp in ("2026-10-20T00:00:00+00:00", "2026-10-21T00:00:00+00:00", "2026-10-21T13:00:00+00:00"):
        collect(state, Fake(), CONFIG, datetime.fromisoformat(stamp))
    row = daily_metrics(state, "2026-10-22T12:00:00+00:00")[-1]
    assert row["complete"] and row["arrivals"] == 0


def test_missing_days_and_unique_prevalence():
    rows = calendar_series(
        [
            {"date": "2026-10-20", "complete": True, "arrivals": 0},
            {"date": "2026-10-22", "complete": True, "arrivals": 3},
        ]
    )
    assert rows[1]["arrivals"] is None
    v = normalize(raw_fixture(required="MLflow MLflow MLflow"), DEMO_TIME, [])
    assert prevalence([v])["MLflow"]["count"] == 1


def test_salaries_never_mix_units_or_open_bounds():
    vacancies = [normalize(raw_fixture(i), DEMO_TIME, []) for i in range(6)]
    vacancies[0].salary.currency = "USD"
    vacancies[1].salary.gross = True
    vacancies[2].salary.lower = None
    groups = salary_groups(vacancies)
    assert len(groups) == 3 and all(g["median"] is None for g in groups)
    same = [normalize(raw_fixture(i), DEMO_TIME, []) for i in range(6)]
    assert salary_groups(same)[0]["median"] is not None


def history(n=70):
    return [
        {
            "date": (datetime(2026, 7, 1, tzinfo=UTC) + timedelta(days=i)).date().isoformat(),
            "complete": True,
            "config_hash": "same",
            "arrivals": i % 7 + 2,
        }
        for i in range(n)
    ]


def test_cold_start_gaps_and_config_changes():
    assert forecast([], "2026-10-22")["status"] == "insufficient"
    rows = history(13)
    assert forecast(rows, "2026-07-14")["predictions"] == []
    rows = history(30)
    for row in rows[-20:]:
        row["complete"] = False
    assert forecast(rows, "2026-08-01")["status"] == "insufficient"
    rows = history(30)
    rows[-1]["config_hash"] = "new"
    assert forecast(rows, "2026-08-01")["status"] == "insufficient"


def test_no_future_leakage_and_models_share_dates():
    rows = history()
    today = rows[-1]["date"]
    before = forecast(rows[:-1], today)
    rows[-1]["arrivals"] = 9999999
    after = forecast(rows, today)
    assert before == after
    assert len(after["predictions"]) == 7
    dates = [v["dates"] for v in after["evaluation"].values()]
    assert all(d == dates[0] for d in dates)
    assert all(p["lower"] >= 0 and p["lower"] <= p["value"] <= p["upper"] for p in after["predictions"])
    assert len(after["evaluation"]) == 2


def test_zero_denominator_wape():
    rows = history(20)
    for row in rows:
        row["arrivals"] = 0
    result = forecast(rows, "2026-07-21")
    assert result["evaluation"]["recent_mean"]["wape"] is None


def test_reclassification_never_rewrites_historical_arrivals(tmp_path):
    state = State(tmp_path / "s", "real")
    collect(state, Fake(), CONFIG, datetime.fromisoformat("2026-10-20T00:00:00+00:00"))
    weak = normalize(
        raw_fixture(
            2,
            title="DevOps Engineer",
            required="Linux",
            responsibilities="Deploy web apps",
            preferred="Terraform",
        ),
        "2026-10-21T00:00:00+00:00",
        [],
    )
    assert weak.category >= 5
    state.observe(weak, "2026-10-21T00:00:00+00:00")
    # Add a run establishing that discovery day's actual observations.
    collect(state, Fake(items=[]), CONFIG, datetime.fromisoformat("2026-10-21T13:00:00+00:00"))
    baseline = daily_metrics(state, "2026-10-22T12:00:00+00:00")[-1]["arrivals"]
    strong = normalize(raw_fixture(2), "2026-10-22T00:00:00+00:00", [])
    state.observe(strong, "2026-10-22T00:00:00+00:00")
    assert daily_metrics(state, "2026-10-22T12:00:00+00:00")[-1]["arrivals"] == baseline


def test_future_search_signature_cannot_affect_past_forecast():
    rows = history(30)
    before = forecast(rows, "2026-07-31")
    after = forecast(
        rows + [{"date": "2026-08-01", "complete": True, "config_hash": "future", "arrivals": 999}],
        "2026-07-31",
    )
    assert before == after
