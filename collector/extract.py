"""Deterministic, section-aware facts; no source HTML is rendered or retained."""

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from collector.models import Salary, Technology, Vacancy

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = json.loads((ROOT / "config/taxonomy.json").read_text())
POLICY = json.loads((ROOT / "config/scoring.json").read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
        if tag in ("p", "li", "br", "h1", "h2", "h3", "div", "strong", "b"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)
        if tag in ("p", "li", "h1", "h2", "h3", "div", "strong", "b"):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain(html):
    parser = TextParser()
    parser.feed(html or "")
    return "\n".join(
        re.sub(r"\s+", " ", line).strip() for line in "".join(parser.parts).splitlines() if line.strip()
    )


HEADINGS = {
    "responsibilities": r"^(?:обязанности|задачи|чем предстоит|что предстоит|responsibilities|what you.ll do)",
    "requirements": r"^(?:требования|мы ожидаем|что ожидаем|вам потребуется|requirements|required skills)",
    "preferred": r"^(?:будет плюсом|желательно|приветствуется|nice.to.have|preferred|optional)",
    "company": r"^(?:о компании|о нас|about us|about the company|условия|мы предлагаем|benefits)",
}


def sections(title, html):
    result = {
        "title": title,
        "responsibilities": "",
        "requirements": "",
        "preferred": "",
        "company": "",
        "unclear": "",
    }
    current = "unclear"
    for line in plain(html).splitlines():
        heading = next((key for key, pattern in HEADINGS.items() if re.search(pattern, line, re.I)), None)
        if heading:
            current = heading
        result[current] += line + "\n"
    return {k: v.strip() for k, v in result.items()}


def extract_technologies(parts):
    matches = []
    for technology in TAXONOMY["technologies"]:
        # Longest aliases first; no substring matches for Go, Ray, MIG, etc.
        alternatives = "|".join(re.escape(a) for a in sorted(technology["aliases"], key=len, reverse=True))
        pattern = re.compile(r"(?<![\w])(?:" + alternatives + r")(?![\w])", re.I)
        for section, text in parts.items():
            for line in re.split(r"[\n]|(?<=[.!?;])\s+", text):
                found = pattern.search(line)
                if not found:
                    continue
                requirement = {
                    "requirements": "required",
                    "preferred": "preferred",
                    "unclear": "unclear",
                }.get(section, "mentioned")
                if re.search(r"будет плюсом|желательно|optional|nice.to.have|preferred", line, re.I):
                    requirement = "preferred"
                if re.search(r"не требуется|не обязател|not required|no experience with", line, re.I):
                    requirement = "mentioned"
                start = max(0, found.start() - 65)
                evidence = line[start : start + 180]
                matches.append(
                    Technology(
                        name=technology["name"],
                        category=technology["category"],
                        matched=found.group(),
                        section=section,
                        requirement=requirement,
                        evidence=evidence,
                    )
                )
                break
    return matches


CORE = r"\b(?:ml[\s-]?ops|llm[\s-]?ops)\b|мл[\s-]?опс"
PLATFORM = r"(?:ml|ai|gpu|мл|ии).{0,25}(?:platform|infrastructure|sre|платформ|инфраструкт)|(?:платформ|инфраструкт).{0,30}(?:машинного обучения|моделей)"
OPS = r"devops|sre|platform|инфраструкт|платформ|эксплуатац|разв[её]рт|сопровожд|deploy|operat|serving|training|инференс|обучени[ея] моделей"


def classify(parts, technologies):
    w = POLICY["weights"]
    title = parts["title"]
    work = parts["responsibilities"] + " " + parts["requirements"]
    substantial = [
        t
        for t in technologies
        if t.category in ("lifecycle", "inference", "gpu")
        and t.section in ("responsibilities", "requirements")
        and t.requirement != "preferred"
        and not re.search(r"не требуется|не обязател|not required|no experience with", t.evidence, re.I)
    ]
    names = sorted({t.name for t in substantial})
    optional = {
        t.name
        for t in technologies
        if t.category in ("lifecycle", "inference", "gpu")
        and t.requirement == "preferred"
        and t.section != "company"
    }
    core = bool(re.search(CORE, title, re.I))
    platform = bool(re.search(PLATFORM, title, re.I))
    operational = bool(names and re.search(OPS, work, re.I))
    score = min(
        100,
        w["core_title"] * core
        + w["platform_title"] * platform
        + w["operational_ml"] * operational
        + min(3, len(names)) * w["ml_technology"]
        + min(2, len(optional)) * w["optional_ml"],
    )
    data = bool(re.search(r"data|данных", title, re.I) and names)
    if data:
        score = min(100, score + w["data_infra"])
    adjacent_title = bool(
        re.search(r"devops|sre|platform|infrastructure|kubernetes|инфраструкт|платформ|девопс", title, re.I)
    )
    adjacent_title = adjacent_title and (not data or bool(re.search(r"devops|sre|девопс", title, re.I)))
    thresholds = POLICY["thresholds"]
    category = (
        1
        if core and score >= thresholds["core"]
        else 2
        if platform and score >= thresholds["platform"]
        else 3
        if operational and adjacent_title and len(names) >= 2 and score >= thresholds["adjacent"]
        else 4
        if data and score >= thresholds["data"]
        else 5
        if score or re.search(r"\bAI\b|\bML\b|ИИ", " ".join(parts.values()), re.I)
        else 6
    )
    reasons = (["core_title"] if core else []) + (["platform_title"] if platform else [])
    reasons += ["operational_ml"] if operational else []
    reasons += ["technology:" + n for n in names]
    negatives = []
    if not names:
        negatives.append("no_explicit_ml_responsibilities")
    if parts["company"] and not names and re.search(r"\bAI\b|\bML\b|ИИ", parts["company"], re.I):
        negatives.append("company_ai_only")
    return category, score, reasons, negatives


def normalize(raw, now, queries):
    title = str(raw.get("name") or "Untitled")
    parts = sections(title, raw.get("description", ""))
    tech = extract_technologies(parts)
    category, score, reasons, negatives = classify(parts, tech)
    work = parts["responsibilities"] + "\n" + parts["requirements"]
    salary_raw = raw.get("salary_range") or raw.get("salary")
    salary = None
    if salary_raw:
        salary = Salary(
            lower=salary_raw.get("from"),
            upper=salary_raw.get("to"),
            currency=salary_raw.get("currency"),
            gross=salary_raw.get("gross"),
            period=(salary_raw.get("frequency") or {}).get("id", "unknown"),
            mode=(salary_raw.get("mode") or {}).get("id", "unknown"),
        )
    experience = (raw.get("experience") or {}).get("id", "unknown")
    seniority = next(
        (x for x in ("junior", "middle", "senior", "lead") if re.search(r"\b" + x + r"\b", title, re.I)),
        "unknown",
    )
    arrangement = [x["id"] for x in raw.get("work_format", []) if x.get("id")] or ["unknown"]
    required = sorted({t.name for t in tech if t.requirement == "required"})
    preferred = sorted({t.name for t in tech if t.requirement == "preferred"})
    ml = sorted(
        {t.name for t in tech if t.category in ("lifecycle", "inference", "gpu") and t.section != "company"}
    )
    employer = raw.get("employer") or {}
    # Persist short evidence only; complete description exists solely in process memory.
    facts = {
        "title": title,
        "employer": employer.get("name", ""),
        "salary": salary.model_dump() if salary else None,
        "arrangement": arrangement,
        "experience": experience,
        "technologies": [t.model_dump() for t in tech],
        "description_hash": digest(parts),
        "location": (raw.get("area") or {}).get("name", ""),
    }
    flags = {
        "gpu": any(
            t.category == "gpu" and t.name not in ("PyTorch", "TensorFlow", "JAX", "Ray")
            for t in tech
            if t.section != "company"
        ),
        "inference": any(t.category == "inference" and t.section != "company" for t in tech),
        "training": bool(re.search(r"distributed training|обучени[ея] моделей|FSDP|DeepSpeed", work, re.I)),
        "llm": bool(re.search(r"\bLLM\b|vLLM|TensorRT-LLM", work, re.I)),
        "kubernetes_ml": any(t.name == "Kubernetes" for t in tech) and bool(ml),
        "transition": category <= 3
        and len(required) > 0
        and any(t.category == "infrastructure" for t in tech),
        "research": bool(re.search(r"research|исследовани|высш.{0,10}математ", work, re.I)),
        "degree": bool(
            re.search(r"PhD|высшее образование|degree required|кандидат наук", parts["requirements"], re.I)
        ),
        "relocation": True if re.search(r"relocation|релокаци", work, re.I) else None,
        "travel": True if re.search(r"business travel|командиров", work, re.I) else None,
        "oncall": True if re.search(r"on.call|дежурств|сменн", work, re.I) else None,
        "english": (
            re.search(r"(?:English|английск\w*)[^.\n]{0,45}", work, re.I).group()
            if re.search(r"(?:English|английск\w*)[^.\n]{0,45}", work, re.I)
            else None
        ),
        "agency": None,
    }
    ru_experience = {
        "noExperience": "без опыта",
        "between1And3": "1–3 года",
        "between3And6": "3–6 лет",
        "moreThan6": "более 6 лет",
    }.get(experience, "неизвестно")
    en_experience = {
        "noExperience": "no experience",
        "between1And3": "1–3 years",
        "between3And6": "3–6 years",
        "moreThan6": "over 6 years",
    }.get(experience, "unknown")
    summary = {
        "ru": f"Область работы: {', '.join(ml) or 'ML-задачи не подтверждены'}. Обязательные навыки: {', '.join(required) or 'не выделены'}. Будет плюсом: {', '.join(preferred) or 'не указано'}. Опыт hh.ru: {ru_experience}.",
        "en": f"Work scope: {', '.join(ml) or 'ML responsibilities unconfirmed'}. Required skills: {', '.join(required) or 'not extracted'}. Preferred: {', '.join(preferred) or 'not stated'}. hh.ru experience: {en_experience}.",
    }
    return Vacancy(
        id=str(raw["id"]),
        url=f"https://hh.ru/vacancy/{raw['id']}",
        title=title,
        employer_id=str(employer.get("id", "unknown")),
        employer=str(employer.get("name", "Unknown")),
        location=facts["location"],
        country=(raw.get("_area_context") or {}).get("country"),
        region=(raw.get("_area_context") or {}).get("region"),
        published_at=raw.get("published_at"),
        created_at=raw.get("created_at"),
        first_seen=now,
        last_seen=now,
        detail_refreshed=now,
        experience=experience,
        seniority=seniority,
        seniority_uncertain=seniority == "unknown",
        years=re.findall(r"\b\d+(?:\s*[-–]\s*\d+)?\s*(?:лет|года?|years?)\b", work, re.I),
        salary=salary,
        category=category,
        score=score,
        reasons=reasons,
        negative_signals=negatives,
        technologies=tech,
        sections={k: v[:180] for k, v in parts.items() if k != "company" and v},
        summary=summary,
        uncertainties=["section_extraction_heuristic"]
        + (["salary_unknown"] if not salary else [])
        + (["arrangement_unknown"] if arrangement == ["unknown"] else [])
        + (["details_missing"] if not raw.get("description") else []),
        flags=flags,
        queries=sorted(queries),
        content_hash=digest(facts),
        description_hash=digest(parts),
        status="archived" if raw.get("archived") is True else "active",
        status_evidence="source_detail",
        found_latest=True,
        arrangement=arrangement,
        employment=(raw.get("employment_form") or raw.get("employment") or {}).get("id"),
        schedule=(raw.get("schedule") or {}).get("id"),
        classifier_version=POLICY["version"],
        extractor_version=TAXONOMY["version"],
    )
