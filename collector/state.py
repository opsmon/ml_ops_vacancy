"""SQLite working index reconstructed from checksummed, partitioned JSON state."""

import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import jsonschema

from collector.extract import ROOT, digest
from collector.models import Event, RunReport, Vacancy


class State:
    def __init__(self, path, mode):
        self.path = Path(path)
        self.mode = mode
        self.vacancies = {}
        self.runs = []
        self.snapshots = []
        self.dictionaries = {}
        self.db = sqlite3.connect(":memory:")
        self.db.executescript("""
            PRAGMA user_version=1;
            CREATE TABLE vacancies(id TEXT PRIMARY KEY, content TEXT NOT NULL);
            CREATE TABLE events(id TEXT, at TEXT, kind TEXT, content TEXT,
                PRIMARY KEY(id, at, kind));
        """)
        if not self.path.exists() and self.path.with_name(self.path.name + ".previous").exists():
            os.replace(self.path.with_name(self.path.name + ".previous"), self.path)
        if (self.path / "manifest.json").exists():
            manifest = json.loads((self.path / "manifest.json").read_text())
            if manifest["schema_version"] != 1 or manifest["mode"] != mode:
                raise ValueError("State schema/mode mismatch: explicit migration required")
            jsonschema.validate(manifest, json.loads((ROOT / "schemas/state-v1.json").read_text()))
            expected = set(manifest["checksums"]) - {"manifest.json"}
            actual = {
                str(f.relative_to(self.path)) for f in self.path.rglob("*.json") if f.name != "manifest.json"
            }
            if expected != actual:
                raise ValueError("Durable state file manifest mismatch")
            for name, checksum in manifest["checksums"].items():
                if Path(name).is_absolute() or ".." in Path(name).parts:
                    raise ValueError("Unsafe durable state path")
                obj = json.loads((self.path / name).read_text())
                if digest(obj) != checksum:
                    raise ValueError("Durable state checksum mismatch")
            for file in sorted((self.path / "vacancies").glob("*.json")):
                v = Vacancy.model_validate_json(file.read_text())
                self.vacancies[v.id] = v
            self.runs = [
                RunReport.model_validate_json(f.read_text())
                for f in sorted((self.path / "runs").glob("*.json"))
            ]
            self.snapshots = [
                json.loads(f.read_text()) for f in sorted((self.path / "snapshots").glob("*.json"))
            ]
            self.dictionaries = json.loads((self.path / "dictionaries.json").read_text())
        for vacancy in self.vacancies.values():
            self.index(vacancy)

    def index(self, vacancy):
        self.db.execute(
            "INSERT OR REPLACE INTO vacancies VALUES (?, ?)", (vacancy.id, vacancy.model_dump_json())
        )
        for event in vacancy.events:
            self.db.execute(
                "INSERT OR REPLACE INTO events VALUES (?, ?, ?, ?)",
                (vacancy.id, event.at, event.kind, event.model_dump_json()),
            )
        self.db.commit()

    def observe(self, vacancy, now, initial=False):
        old = self.vacancies.get(vacancy.id)
        fields = []
        kind = "initial_inventory" if initial else "discovered"
        if old:
            vacancy.first_seen = old.first_seen
            vacancy.queries = sorted(set(old.queries + vacancy.queries))
            vacancy.events = old.events.copy()
            for field in (
                "title",
                "salary",
                "technologies",
                "description_hash",
                "arrangement",
                "status",
                "category",
                "published_at",
                "employer_id",
            ):
                if old.model_dump()[field] != vacancy.model_dump()[field]:
                    fields.append(field)
            kind = "updated"
        if not old or fields:
            before = {f: old.model_dump()[f] for f in fields if f != "technologies"} if old else {}
            after = {f: vacancy.model_dump()[f] for f in fields if f != "technologies"}
            after.update(
                category=vacancy.category, employer_id=vacancy.employer_id, published_at=vacancy.published_at
            )
            if "technologies" in fields:
                before["technologies"] = sorted({t.name for t in old.technologies})
                after["technologies"] = sorted({t.name for t in vacancy.technologies})
            vacancy.events.append(Event(at=now, kind=kind, fields=fields, before=before, after=after))
        self.vacancies[vacancy.id] = vacancy
        self.index(vacancy)
        return "new" if not old else "changed" if fields else "unchanged"

    def reposts(self):
        groups = {}
        for v in self.vacancies.values():
            key = (v.employer_id, v.title.casefold().strip())
            groups.setdefault(key, []).append(v.id)
        for ids in groups.values():
            for source_id in ids:
                self.vacancies[source_id].possible_reposts = [x for x in ids if x != source_id]

    def save(self):
        """Directory replacement locally; git commit is the remote atomic publication boundary."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.runs:
            cutoff = (
                max(datetime.fromisoformat(r.finished_at) for r in self.runs) - timedelta(days=366)
            ).isoformat()
            self.runs = [r for r in self.runs if r.finished_at >= cutoff]
            self.snapshots = [s for s in self.snapshots if s["at"] >= cutoff]
        staging = Path(tempfile.mkdtemp(prefix=".mlpops-", dir=self.path.parent))
        checksums = {}

        def write(name, obj):
            file = staging / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
            checksums[name] = digest(obj)

        for v in sorted(self.vacancies.values(), key=lambda v: v.id):
            write(f"vacancies/{v.id}.json", v.model_dump())
        for r in self.runs:
            write(f"runs/{r.id}.json", r.model_dump())
        for snapshot in self.snapshots:
            write(f"snapshots/{snapshot['id']}.json", snapshot)
        write("dictionaries.json", self.dictionaries)
        write("manifest.json", {"schema_version": 1, "mode": self.mode, "checksums": checksums})
        backup = self.path.with_name(self.path.name + ".previous")
        if backup.exists():
            shutil.rmtree(backup)
        if self.path.exists():
            os.replace(self.path, backup)
        try:
            os.replace(staging, self.path)
        except OSError:
            if backup.exists():
                os.replace(backup, self.path)
            raise
        if backup.exists():
            shutil.rmtree(backup)
