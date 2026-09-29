"""Seed and retrieve structured historical incident cases for SRE reasoning."""
import re
import logging
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from .demo_incident_cases import DEMO_INCIDENT_CASES
from .db import SessionLocal
from .models import IncidentCase

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "about", "after", "again", "against", "also", "because", "before", "being", "between", "could",
    "does", "during", "from", "have", "into", "issue", "issues", "just", "more", "most", "other",
    "over", "same", "some", "than", "that", "their", "there", "these", "they", "this", "those",
    "through", "under", "very", "what", "when", "where", "which", "while", "with", "would",
}


def _search_text(record):
    fields = [record["category"], record["service"], record["title"], record["root_cause"]]
    fields.extend(record["symptoms"])
    fields.extend(record["tags"])
    fields.extend(record["remediation"])
    return " ".join(str(value) for value in fields).casefold()


def seed_demo_cases():
    with SessionLocal() as db:
        existing = set(db.scalars(select(IncidentCase.case_id)).all())
        new_cases = []
        for record in DEMO_INCIDENT_CASES:
            if record["case_id"] in existing:
                continue
            new_cases.append(IncidentCase(**record, search_text=_search_text(record)))
        if new_cases:
            db.add_all(new_cases)
            db.commit()
        return {"inserted": len(new_cases), "total": len(existing) + len(new_cases)}


def incident_case_stats():
    with SessionLocal() as db:
        records = db.scalars(select(IncidentCase)).all()
        categories = {}
        for record in records:
            categories[record.category] = categories.get(record.category, 0) + 1
        return {"count": len(records), "categories": categories,
                "synthetic_count": sum(1 for record in records if record.synthetic)}


def search_incident_cases(query, limit=3):
    terms = {term for term in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", query.casefold())
             if term not in STOP_WORDS and not term.startswith("syn-")}
    if not terms:
        return []
    try:
        with SessionLocal() as db:
            records = db.scalars(select(IncidentCase).limit(1000)).all()
    except SQLAlchemyError:
        logger.warning("Incident case retrieval is unavailable; continuing without historical context.")
        return []
    ranked = []
    for record in records:
        text = record.search_text.casefold()
        matched = {term for term in terms if term in text}
        if not matched:
            continue
        title_terms = {term for term in terms if term in record.title.casefold()}
        cause_terms = {term for term in terms if term in record.root_cause.casefold()}
        score = len(matched) + (2 * len(title_terms)) + len(cause_terms)
        ranked.append((score, record.case_id, record, sorted(matched)))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [{
        "case_id": record.case_id,
        "category": record.category,
        "service": record.service,
        "severity": record.severity,
        "title": record.title,
        "symptoms": record.symptoms,
        "metrics": record.metrics,
        "root_cause": record.root_cause,
        "remediation": record.remediation,
        "verification": record.verification,
        "tags": record.tags,
        "synthetic": record.synthetic,
        "retrieval_score": score,
        "matched_terms": matched,
    } for score, _, record, matched in ranked[:limit]]
