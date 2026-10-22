import json
from datetime import datetime, timedelta

import httpx
import pytest

from collector.api import AccessFailure, CollectionError, HHClient
from collector.demo import DEMO_TIME, raw_fixture
from collector.models import Dataset, RunReport
from collector.pipeline import collect, export, search, write_export
from collector.state import State

NOW = datetime.fromisoformat(DEMO_TIME)
CONFIG = {
    "version": "test",
    "lookback_days": 1,
    "queries": [{"id": "q1", "text": "MLOps"}, {"id": "q2", "text": "ML Ops"}],
}


class Fake:
    def __init__(self, items=None, fail=False, archived=False):
        self.count = 0
        self.items = items if items is not None else [raw_fixture()]
        self.fail, self.archived = fail, archived

    def get(self, path, params=None):
        self.count += 1
        if self.fail:
            raise AccessFailure("no token")
        if path == "/areas":
            return [{"id": "113", "name": "Россия", "areas": [{"id": "1", "name": "Москва", "areas": []}]}]
        if path == "/dictionaries":
            return {"experience": [{"id": "noExperience"}]}
        if path == "/vacancies":
            return {"items": self.items, "found": len(self.items), "pages": 1}
        return raw_fixture(archived=self.archived)


def report():
    return RunReport(
        id="test",
        started_at=DEMO_TIME,
        finished_at=DEMO_TIME,
        status="complete",
        initial_inventory=True,
        config_hash="x",
        taxonomy_version="1",
    )


def test_partition_overlap_and_unresolved_truncation():
    class Large:
        def get(self, path, params):
            seconds = (
                datetime.fromisoformat(params["date_to"]) - datetime.fromisoformat(params["date_from"])
            ).total_seconds()
            return {"found": 2100 if seconds > 300 else 1, "pages": 1, "items": [{"id": "1"}]}

    r = report()
    results = list(search(Large(), CONFIG["queries"][0], NOW, NOW + timedelta(hours=1), r))
    assert results and not r.truncations and r.pages > 1
    leaves = [p for p in r.partitions if p["found"] == 1]
    for left, right in zip(leaves, leaves[1:], strict=False):
        assert left["to"] == right["from"]

    class AlwaysLarge:
        def get(self, path, params):
            return {"found": 3000, "pages": 999, "items": []}

    r = report()
    list(search(AlwaysLarge(), CONFIG["queries"][0], NOW, NOW + timedelta(minutes=5), r))
    assert len(r.truncations) == 1 and r.pages == 20


def test_incremental_dedup_and_idempotency(tmp_path):
    state = State(tmp_path / "state", "real")
    run = collect(state, Fake(), CONFIG, NOW)
    assert run.status == "complete" and run.unique_ids == 1 and run.duplicates == 1
    assert state.vacancies["demo-1"].queries == ["q1", "q2"]
    state.save()
    restored = State(tmp_path / "state", "real")
    assert len(restored.vacancies) == 1
    same = collect(restored, Fake(), CONFIG, NOW)
    assert same.id == run.id and len(restored.runs) == 1
    assert restored.db.execute("SELECT count(*) FROM vacancies").fetchone()[0] == 1
    collect(restored, Fake(), CONFIG, NOW + timedelta(days=1))
    assert len(restored.vacancies["demo-1"].events) == 1
    assert restored.vacancies["demo-1"].first_seen == DEMO_TIME


def test_missing_search_does_not_archive_and_source_can_archive(tmp_path):
    state = State(tmp_path / "state", "real")
    collect(state, Fake(), CONFIG, NOW)
    collect(state, Fake(items=[]), CONFIG, NOW + timedelta(hours=6))
    assert state.vacancies["demo-1"].status == "active"
    assert state.vacancies["demo-1"].found_latest is False
    collect(state, Fake(items=[], archived=True), CONFIG, NOW + timedelta(days=2))
    assert state.vacancies["demo-1"].status == "archived"
    assert state.vacancies["demo-1"].events[-1].after["status"] == "archived"


def test_failed_collection_rolls_back_and_preserves_export(tmp_path):
    state = State(tmp_path / "state", "real")
    collect(state, Fake(), CONFIG, NOW)
    path = tmp_path / "data.json"
    write_export(export(state, DEMO_TIME), path)
    old = path.read_bytes()
    run = collect(state, Fake(fail=True), CONFIG, NOW + timedelta(days=1))
    assert run.status == "failed" and len(state.vacancies) == 1
    assert path.read_bytes() == old and len(state.snapshots) == 1
    state.save()
    assert State(tmp_path / "state", "real").runs[-1].status == "failed"
    assert export(state, (NOW + timedelta(days=1)).isoformat()).daily[-1]["arrivals"] is None


def test_partial_failure_not_labeled_complete(tmp_path):
    class Partial(Fake):
        def get(self, path, params=None):
            if path == "/vacancies" and params["text"] == "ML Ops":
                raise CollectionError("budget")
            return super().get(path, params)

    state = State(tmp_path / "s", "real")
    r = collect(state, Partial(), CONFIG, NOW)
    assert r.status == "partial" and not state.vacancies and not state.snapshots


def test_state_mode_checksum_and_schema_gates(tmp_path):
    state = State(tmp_path / "s", "real")
    collect(state, Fake(), CONFIG, NOW)
    state.save()
    with pytest.raises(ValueError, match="mode mismatch"):
        State(state.path, "demo")
    f = next((state.path / "vacancies").glob("*.json"))
    obj = json.loads(f.read_text())
    obj["title"] = "tampered"
    f.write_text(json.dumps(obj))
    with pytest.raises(ValueError, match="checksum"):
        State(state.path, "real")


def test_publication_gate_and_archival_removal(tmp_path, monkeypatch):
    state = State(tmp_path / "s", "real")
    collect(state, Fake(), CONFIG, NOW)
    monkeypatch.delenv("HH_PUBLICATION_PERMISSION", raising=False)
    with pytest.raises(PermissionError):
        export(state, DEMO_TIME, public=True)
    monkeypatch.setenv("HH_PUBLICATION_PERMISSION", "written-approval-reference")
    collect(state, Fake(archived=True), CONFIG, NOW + timedelta(days=2))
    data = export(state, DEMO_TIME, public=True)
    assert not data.vacancies and all(not s["vacancies"] for s in data.snapshots)
    Dataset.model_validate_json(data.model_dump_json())


def client(handler, budget=10, sleep=lambda _: None):
    return HHClient(
        token="secret-canary",
        user_agent="MlPops/1 (developer@valid.test)",
        budget=budget,
        transport=httpx.MockTransport(handler),
        sleep=sleep,
    )


def test_auth_and_captcha_never_leak_secrets():
    for code, body in [
        (401, {}),
        (403, {}),
        (403, {"errors": [{"value": "captcha_required", "captcha_url": "secret-canary"}]}),
    ]:
        c = client(lambda _, code=code, body=body: httpx.Response(code, json=body))
        with pytest.raises(AccessFailure) as err:
            c.get("/vacancies")
        assert "secret-canary" not in str(err.value)
        c.close()


def test_retry_after_budget_and_transport():
    calls, waits = [], []

    def handler(request):
        calls.append(request)
        return (
            httpx.Response(429, headers={"Retry-After": "2"}, json={})
            if len(calls) == 1
            else httpx.Response(200, json={"items": []})
        )

    c = client(handler, sleep=waits.append)
    assert c.get("/vacancies") == {"items": []}
    assert c.count == 2 and waits[0] >= 2
    c.close()
    c = client(lambda _: httpx.Response(500), budget=1)
    with pytest.raises(CollectionError, match="budget"):
        c.get("/vacancies")
    c.close()


def test_credentialed_client_rejects_external_url():
    c = client(lambda _: httpx.Response(200, json={}))
    with pytest.raises(CollectionError):
        c.get("https://evil.test")
    c.close()


def test_inaccessible_is_not_archival(tmp_path):
    from collector.api import Unavailable

    class Gone(Fake):
        def get(self, path, params=None):
            if path.startswith("/vacancies/"):
                raise Unavailable("404")
            return super().get(path, params)

    state = State(tmp_path / "s", "real")
    collect(state, Fake(), CONFIG, NOW)
    collect(state, Gone(items=[]), CONFIG, NOW + timedelta(days=2))
    v = state.vacancies["demo-1"]
    assert v.status == "inaccessible" and "not_archival" in v.status_evidence
    assert not any(e.after.get("status") == "archived" for e in v.events)


def test_real_cli_without_credentials_records_failure(tmp_path, monkeypatch):
    from collector.pipeline import run_real

    monkeypatch.delenv("HH_TOKEN", raising=False)
    output = tmp_path / "market.json"
    assert run_real(tmp_path / "s", output) == 1
    assert not output.exists()
    assert State(tmp_path / "s", "real").runs[-1].status == "failed"


def test_lookback_changes_coverage_signature(tmp_path):
    a = collect(State(tmp_path / "a", "real"), Fake(), CONFIG, NOW, days=1)
    b = collect(State(tmp_path / "b", "real"), Fake(), CONFIG, NOW, days=30)
    assert a.config_hash != b.config_hash
