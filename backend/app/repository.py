from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from .db import SessionLocal
from .models import Approval, AuditEvent, Integration, Investigation

def now():
    return datetime.now(timezone.utc)

class Repository:
    def create_investigation(self, inv_id, payload):
        with SessionLocal() as db:
            db.add(Investigation(id=inv_id, application=payload["application"], environment=payload["environment"], query=payload["query"], status="running", result={}))
            db.commit()

    def save_investigation_result(self, inv_id, result):
        with SessionLocal() as db:
            obj = db.get(Investigation, inv_id)
            if obj:
                obj.status = result.get("status", "completed")
                obj.root_cause = result.get("root_cause")
                obj.confidence = result.get("confidence_score")
                obj.result = result
                obj.updated_at = now()
                db.commit()

    def list_investigations(self, limit=50):
        with SessionLocal() as db:
            rows = db.scalars(select(Investigation).order_by(Investigation.created_at.desc()).limit(limit)).all()
            return [{"id": x.id, "application": x.application, "environment": x.environment, "status": x.status, "root_cause": x.root_cause, "confidence": x.confidence, "created_at": x.created_at.isoformat()} for x in rows]

    def get_investigation(self, inv_id):
        with SessionLocal() as db:
            x = db.get(Investigation, inv_id)
            if not x:
                return None
            return {"id": x.id, "application": x.application, "environment": x.environment, "query": x.query, "status": x.status, "root_cause": x.root_cause, "confidence": x.confidence, "result": x.result, "created_at": x.created_at.isoformat()}

    def create_approval(self, investigation_id, action, environment, risk):
        approval_id = f"APR-{uuid4().hex[:8].upper()}"
        with SessionLocal() as db:
            db.add(Approval(id=approval_id, investigation_id=investigation_id, action=action, environment=environment, risk=risk, status="pending"))
            db.commit()
        self.audit("approval.requested", "orchestrator-agent", approval_id, {"investigation_id": investigation_id, "action": action, "risk": risk})
        return approval_id

    def list_approvals(self):
        with SessionLocal() as db:
            rows = db.scalars(select(Approval).order_by(Approval.created_at.desc())).all()
            return [{"id": x.id, "investigation_id": x.investigation_id, "action": x.action, "environment": x.environment, "risk": x.risk, "status": x.status, "decided_by": x.decided_by, "comment": x.comment, "created_at": x.created_at.isoformat()} for x in rows]

    def decide_approval(self, approval_id, status, decided_by, comment):
        with SessionLocal() as db:
            x = db.get(Approval, approval_id)
            if not x:
                return None
            x.status = status
            x.decided_by = decided_by
            x.comment = comment
            x.decided_at = now()
            db.commit()
            result = {"id": x.id, "investigation_id": x.investigation_id, "status": x.status, "action": x.action, "environment": x.environment}
        self.audit(f"approval.{status}", decided_by, approval_id, result)
        return result

    def add_integration(self, provider, name, configuration, enabled):
        integration_id = f"INT-{uuid4().hex[:8].upper()}"
        safe_config = {k: v for k, v in configuration.items() if not any(s in k.lower() for s in ("token", "password", "secret"))}
        with SessionLocal() as db:
            db.add(Integration(id=integration_id, provider=provider, name=name, configuration=safe_config, enabled=enabled))
            db.commit()
        self.audit("integration.created", "user", integration_id, {"provider": provider, "name": name})
        return integration_id

    def list_integrations(self):
        with SessionLocal() as db:
            rows = db.scalars(select(Integration).order_by(Integration.created_at.desc())).all()
            return [{"id": x.id, "provider": x.provider, "name": x.name, "configuration": x.configuration, "enabled": x.enabled} for x in rows]

    def audit(self, event_type, actor, entity_id, payload):
        with SessionLocal() as db:
            db.add(AuditEvent(id=f"AUD-{uuid4().hex[:10].upper()}", event_type=event_type, actor=actor, entity_id=entity_id, payload=payload))
            db.commit()

repo = Repository()
