import pytest

from collector.demo import DEMO_TIME, demo_dataset, raw_fixture
from collector.extract import classify, extract_technologies, normalize, plain, sections


def names(text):
    return {t.name for t in extract_technologies({"requirements": text})}


def test_aliases_boundaries_and_triton_disambiguation():
    assert names("k8s, Golang, ArgoCD, OTel, Postgres") >= {
        "Kubernetes",
        "Go",
        "Argo CD",
        "OpenTelemetry",
        "PostgreSQL",
    }
    assert not names("Django, migration, array, Triton programming language") & {
        "Go",
        "MIG",
        "Ray",
        "NVIDIA Triton Inference Server",
    }
    assert "NVIDIA Triton Inference Server" in names("NVIDIA Triton Inference Server")
    assert "TensorRT-LLM" in names("TensorRT-LLM")


def test_required_preferred_sections_and_optional_override():
    vacancy = normalize(
        raw_fixture(required="Linux, Kubernetes. Желательно Python", preferred="ClearML"), DEMO_TIME, []
    )
    assert any(t.name == "Kubernetes" and t.requirement == "required" for t in vacancy.technologies)
    assert all(t.requirement == "preferred" for t in vacancy.technologies if t.name == "ClearML")
    assert any(t.name == "Python" and t.requirement == "preferred" for t in vacancy.technologies)
    assert all(t.evidence and t.matched and len(t.evidence) <= 180 for t in vacancy.technologies)


def test_company_ai_does_not_promote_generic_devops():
    parts = sections(
        "DevOps Engineer",
        "<h3>О компании</h3><p>AI MLflow платформа</p><h3>Требования</h3><p>Python Kubernetes</p>",
    )
    category, score, _, negative = classify(parts, extract_technologies(parts))
    assert category >= 5
    assert score == 0
    assert "company_ai_only" in negative


def test_adjacent_role_without_mlops_title():
    v = normalize(
        raw_fixture(
            title="DevOps Engineer",
            required="Kubernetes, MLflow, KServe",
            responsibilities="Эксплуатация MLflow и KServe",
        ),
        DEMO_TIME,
        [],
    )
    assert v.category == 3 and v.score >= 45
    assert "operational_ml" in v.reasons


def test_html_is_text_and_never_executable():
    text = plain("<script>alert(1)</script><style>x</style><p>&lt;img onerror=bad&gt;</p>")
    assert "alert" not in text and "<img" in text
    v = normalize(raw_fixture(description="<p>Linux</p><script>token</script>"), DEMO_TIME, [])
    assert "token" not in v.model_dump_json()


def test_unknown_fields_and_bilingual_summary():
    v = normalize({"id": "123", "new_field": "new"}, DEMO_TIME, [])
    assert v.salary is None and v.arrangement == ["unknown"]
    assert v.flags["oncall"] is None and v.flags["agency"] is None
    assert set(v.summary) == {"ru", "en"}
    assert "details_missing" in v.uncertainties


def test_demo_is_fictional_and_no_fake_forecast():
    data = demo_dataset()
    assert data.mode == "demo" and all("DEMO" in v.employer for v in data.vacancies)
    assert data.forecast["predictions"] == []
    assert not data.snapshots
    assert data.daily[0]["arrivals"] is None


@pytest.mark.parametrize("text", ["Kubernetes Python Linux", "AI-driven company", "We use Go and Docker"])
def test_generic_infrastructure_is_not_mlops(text):
    parts = sections("DevOps Engineer", text)
    assert classify(parts, extract_technologies(parts))[0] >= 5


def test_negated_ml_requirements_do_not_promote_role():
    v = normalize(
        raw_fixture(
            title="DevOps Engineer",
            responsibilities="Deploy web applications",
            required="Не требуется CUDA, MLflow",
            preferred="Terraform",
        ),
        DEMO_TIME,
        [],
    )
    assert v.category >= 5 and v.score == 0
