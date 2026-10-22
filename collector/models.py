"""Versioned public contracts. Raw source HTML and contacts are never exported."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Technology(Contract):
    name: str
    category: str
    matched: str
    section: Literal["title", "responsibilities", "requirements", "preferred", "company", "unclear"]
    requirement: Literal["required", "preferred", "mentioned", "unclear"]
    evidence: str = Field(max_length=180)


class Salary(Contract):
    lower: float | None = None
    upper: float | None = None
    currency: str | None = None
    gross: bool | None = None
    period: str = "unknown"
    mode: str = "unknown"


class Event(Contract):
    at: str
    kind: str
    fields: list[str] = []
    before: dict = {}
    after: dict = {}


class Vacancy(Contract):
    id: str = Field(pattern=r"^(?:[0-9]+|demo-[0-9]+)$")
    url: str
    title: str
    employer_id: str
    employer: str
    location: str = ""
    country: str | None = None
    region: str | None = None
    arrangement: list[str] = ["unknown"]
    employment: str | None = None
    schedule: str | None = None
    published_at: str | None = None
    created_at: str | None = None
    first_seen: str
    last_seen: str
    detail_refreshed: str | None = None
    experience: str = "unknown"
    seniority: str = "unknown"
    seniority_uncertain: bool = True
    years: list[str] = []
    salary: Salary | None = None
    category: int = Field(ge=1, le=6)
    score: int = Field(ge=0, le=100)
    reasons: list[str] = []
    negative_signals: list[str] = []
    technologies: list[Technology] = []
    sections: dict[str, str] = {}
    summary: dict[str, str]
    uncertainties: list[str] = []
    flags: dict[str, bool | str | None] = {}
    queries: list[str] = []
    content_hash: str
    description_hash: str
    status: Literal["active", "archived", "inaccessible", "unknown"] = "unknown"
    status_evidence: str = ""
    found_latest: bool | None = None
    possible_reposts: list[str] = []
    events: list[Event] = []
    classifier_version: str
    extractor_version: str


class RunReport(Contract):
    id: str
    started_at: str
    finished_at: str
    status: Literal["complete", "partial", "failed"]
    initial_inventory: bool
    config_hash: str
    taxonomy_version: str
    queries: list[str] = []
    partitions: list[dict] = []
    pages: int = 0
    requests: int = 0
    unique_ids: int = 0
    details_refreshed: int = 0
    details_unavailable: int = 0
    new: int = 0
    changed: int = 0
    archived: int = 0
    duplicates: int = 0
    truncations: list[dict] = []
    failures: list[str] = []
    export_validated: bool = False


class Dataset(Contract):
    schema_version: Literal[1] = 1
    mode: Literal["demo", "real"]
    generated_at: str
    last_success: str | None
    coverage: Literal["complete", "partial", "failed", "none"]
    config_hash: str
    vacancies: list[Vacancy]
    runs: list[RunReport]
    daily: list[dict]
    snapshots: list[dict]
    forecast: dict
    methodology_version: str = "1.0.0"
    taxonomy: list[dict]
    dictionaries: dict = {}
