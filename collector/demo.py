"""Fictional, deterministic inventory; no fabricated market time series."""

from collector.extract import TAXONOMY, normalize
from collector.models import Event, RunReport
from collector.pipeline import export
from collector.state import State

DEMO_TIME = "2026-10-22T12:00:00+00:00"


def raw_fixture(
    index=1,
    title="MLOps Engineer",
    required="Linux, Kubernetes, Python, MLflow",
    responsibilities="Эксплуатация MLflow и KServe: model serving в Kubernetes",
    preferred="ClearML, Terraform",
    **extra,
):
    value = {
        "id": f"demo-{index}",
        "name": title,
        "employer": {
            "id": f"fiction-{(index - 1) % 5}",
            "name": [
                "Синтетика Лаб • DEMO",
                "Fictional Orbit • DEMO",
                "Учебный Контур • DEMO",
                "Example GPU • DEMO",
                "Вымышленный Банк • DEMO",
            ][(index - 1) % 5],
        },
        "area": {"id": "1", "name": "Москва" if index % 3 else "Санкт-Петербург"},
        "description": f"<h3>Обязанности</h3><p>{responsibilities}</p><h3>Требования</h3><p>{required}</p><h3>Будет плюсом</h3><p>{preferred}</p>",
        "published_at": f"2026-10-{22 - index % 7:02d}T08:00:00+03:00",
        "created_at": "2026-10-14T08:00:00+03:00",
        "archived": False,
        "experience": {"id": "between3And6" if index % 3 else "between1And3"},
        "work_format": [{"id": "REMOTE" if index % 2 else "HYBRID"}],
        "salary_range": {
            "from": 250000 + index * 10000,
            "to": 350000 + index * 10000,
            "currency": "RUR",
            "gross": False,
            "frequency": {"id": "MONTHLY"},
            "mode": {"id": "MONTH"},
        },
        "employment_form": {"id": "FULL"},
    }
    value.update(extra)
    return value


def demo_dataset():
    state = State("/nonexistent/mlpops-demo-state", "demo")
    fixtures = [
        raw_fixture(1),
        raw_fixture(
            2,
            "DevOps / ML Platform",
            "Linux, Kubernetes, Helm, Prometheus, Terraform",
            "Развертывание MLflow и GPU Operator, эксплуатация inference платформы",
            "vLLM, Ray Serve",
        ),
        raw_fixture(
            3,
            "Senior GPU Infrastructure Engineer",
            "Linux, CUDA, NCCL, Slurm, InfiniBand, Python, English B2",
            "Эксплуатация GPU-кластера, distributed training PyTorch, DCGM",
            "DeepSpeed, FSDP, MIG",
            salary_range=None,
        ),
        raw_fixture(
            4,
            "SRE — inference platform",
            "Kubernetes, KServe, NVIDIA Triton Inference Server, Grafana, Go",
            "Deploy model serving with KServe and TensorRT-LLM, on-call",
            "OpenTelemetry, Ray Serve",
        ),
        raw_fixture(
            5,
            "Junior MLOps Engineer",
            "Python, Linux, Docker, MLflow",
            "Сопровождение ML pipelines и model registry",
            "DVC, ClearML",
            experience={"id": "noExperience"},
            salary_range={"from": 120000, "to": None, "currency": "RUR", "gross": True},
        ),
        raw_fixture(
            6,
            "Data Platform Engineer",
            "Kafka, Spark, S3, Airflow, PostgreSQL",
            "Обслуживание feature store Feast, ML pipelines",
            "Flink, ClickHouse",
            work_format=[],
        ),
        raw_fixture(
            7,
            "LLMOps Engineer",
            "vLLM, Kubernetes, CUDA, TensorRT-LLM, Python",
            "Эксплуатация LLM serving, GPU sharing и model serving",
            "Qdrant, Kueue",
            salary_range={
                "from": 5000,
                "to": 7000,
                "currency": "USD",
                "gross": None,
                "frequency": {"id": "MONTHLY"},
            },
        ),
        raw_fixture(
            8,
            "DevOps Engineer",
            "Kubernetes, Linux, Python, GitLab CI",
            "Эксплуатация веб-сервисов и CI/CD",
            "Terraform",
            description="<h3>О компании</h3><p>Мы создаём AI продукты.</p><h3>Обязанности</h3><p>Эксплуатация веб-сервисов</p><h3>Требования</h3><p>Kubernetes, Python, Linux</p>",
        ),
        raw_fixture(
            9,
            "Platform Engineer",
            "Kubernetes, Linux, Argo CD, ClearML, MLflow",
            "Эксплуатация ClearML и MLflow; ML pipelines",
            "Kubeflow, MinIO",
        ),
        raw_fixture(
            10,
            "Research Engineer",
            "Python, Triton programming language, PhD, высшая математика",
            "Исследование алгоритмов",
            "PyTorch",
            salary_range=None,
        ),
        raw_fixture(
            11,
            "ML Platform Engineer",
            "OpenShift AI, Kubeflow, KServe, Helm, Linux",
            "Эксплуатация ML platform, distributed training",
            "Volcano, KubeRay",
        ),
        raw_fixture(
            12,
            "MLOps Engineer",
            "Linux, Kubernetes, Python, MLflow",
            "Эксплуатация MLflow и KServe: model serving в Kubernetes",
            "ClearML",
            archived=True,
        ),
    ]
    for raw in fixtures:
        vacancy = normalize(raw, DEMO_TIME, {"demo-fixture"})
        state.observe(vacancy, DEMO_TIME, initial=True)
    changed = state.vacancies["demo-2"]
    changed.events.append(
        Event(
            at=DEMO_TIME,
            kind="updated",
            fields=["salary"],
            before={"salary": {**changed.salary.model_dump(), "lower": 240000, "upper": 340000}},
            after={"salary": changed.salary.model_dump()},
        )
    )
    state.vacancies["demo-12"].employer_id = state.vacancies["demo-1"].employer_id
    state.reposts()
    state.runs.append(
        RunReport(
            id="demo-inventory",
            started_at=DEMO_TIME,
            finished_at=DEMO_TIME,
            status="complete",
            initial_inventory=True,
            config_hash="demo-v1",
            taxonomy_version=TAXONOMY["version"],
            unique_ids=len(fixtures),
            details_refreshed=len(fixtures),
            new=len(fixtures),
            export_validated=True,
        )
    )
    return export(state, DEMO_TIME)
