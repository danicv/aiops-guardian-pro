"""Feedback on retrieved precedents, used to re-rank future retrievals."""
from sqlalchemy import func, select
from .db import SessionLocal
from .models import CaseFeedback, IncidentCase

MAX_NET = 3        # one vote cannot dominate and a long history cannot lock a case in or out
WEIGHT_PER_VOTE = 0.15


def record_feedback(case_id, helpful, investigation_id=None):
    with SessionLocal() as db:
        if db.get(IncidentCase, case_id) is None:
            raise LookupError(f"Unknown incident case {case_id}.")
        db.add(CaseFeedback(case_id=case_id, investigation_id=investigation_id, rating=1 if helpful else -1))
        db.commit()
    return {"case_id": case_id, "rating": "helpful" if helpful else "not_helpful",
            "net_votes": case_adjustments().get(case_id, 0)}


def case_adjustments():
    """Net helpful votes per case, clamped to +/- MAX_NET."""
    with SessionLocal() as db:
        rows = db.execute(select(CaseFeedback.case_id, func.sum(CaseFeedback.rating))
                          .group_by(CaseFeedback.case_id)).all()
    return {case_id: max(-MAX_NET, min(MAX_NET, int(total))) for case_id, total in rows}


def adjustment_factor(net_votes):
    return 1 + WEIGHT_PER_VOTE * net_votes
