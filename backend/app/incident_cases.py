"""Seed and retrieve structured historical incident cases for SRE reasoning."""
import re
import logging
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from .demo_incident_cases import DEMO_INCIDENT_CASES
from .config import settings
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
    return [_as_result(record, score, matched, "lexical") for score, _, record, matched in ranked[:limit]]


def _as_result(record, score, matched, method):
    return {
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
        "retrieval_method": method,
    }


def semantic_search_incident_cases(query, limit=3):
    """Embedding similarity search. Cases below the similarity floor are dropped, so unrelated queries return nothing."""
    from . import embeddings
    with SessionLocal() as db:
        records = db.scalars(select(IncidentCase).limit(1000)).all()
    if not records or not query.strip():
        return []
    vectors = embeddings.embed([query] + [record.search_text for record in records])
    ranked = sorted(((embeddings.cosine(vectors[0], vector), record.case_id, record)
                     for vector, record in zip(vectors[1:], records)), key=lambda item: (-item[0], item[1]))
    return [_as_result(record, round(score, 4), [], "embedding") for score, _, record in ranked[:limit]
            if score >= settings.embedding_min_similarity]


def retrieve_cases(query, limit=3):
    """Retrieval used by the agents: embeddings when configured (lexical fallback), then feedback re-ranking."""
    from . import embeddings, feedback
    candidates = []
    if embeddings.enabled():
        try:
            candidates = semantic_search_incident_cases(query, limit=limit * 3)
        except Exception as error:
            logger.warning("Embedding retrieval failed (%s); falling back to lexical search.", type(error).__name__)
            candidates = search_incident_cases(query, limit=limit * 3)
    else:
        candidates = search_incident_cases(query, limit=limit * 3)
    try:
        votes = feedback.case_adjustments()
    except SQLAlchemyError:
        votes = {}
    for case in candidates:
        net = votes.get(case["case_id"], 0)
        case["feedback_net"] = net
        case["retrieval_score"] = round(case["retrieval_score"] * feedback.adjustment_factor(net), 4)
    candidates.sort(key=lambda case: (-case["retrieval_score"], case["case_id"]))
    return candidates[:limit]
